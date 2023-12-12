import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401

import base64
import os
import pychrome
import requests
import subprocess
import tempfile
import threading
import time
import traceback
from enum import Enum
from threading import Event

from pdf2image import convert_from_path
from PIL import Image
from PyPDF2 import PdfReader


# region constants and configurations

# Chrome respects proxy env params
handle_proxy()
# Make sure our python code doesn't go through a proxy when communicating with chrome webdriver
os.environ['no_proxy'] = 'localhost,127.0.0.1'
# Needed for cases that rasterize is running with non-root user (docker hardening)
os.environ['HOME'] = tempfile.gettempdir()

CHROME_EXE = os.getenv('CHROME_EXE', '/opt/google/chrome/google-chrome')

WITH_ERRORS = demisto.params().get('with_error', True)

# The default wait time before taking a screenshot
DEFAULT_WAIT_TIME = max(int(demisto.params().get('wait_time', 0)), 0)
DEFAULT_PAGE_LOAD_TIME = int(demisto.params().get('max_page_load_time', 180))

# Used it in several places
DEFAULT_RETRIES_COUNT = 3
DEFAULT_RETRY_WAIT_IN_SECONDS = 2
PAGES_LIMITATION = 20

# TODO Make instance param
MAX_CHROMES_COUNT = 32

# Polling for rasterization commands to complete
DEFAULT_POLLING_INTERVAL = 0.1

# Consts for custom width and height
MAX_FULLSCREEN_WIDTH = 8000
MAX_FULLSCREEN_HEIGHT = 8000
DEFAULT_WIDTH, DEFAULT_HEIGHT = 600, 800

# Local Chrome
LOCAL_CHROME_HOST = "127.0.0.1"


class RasterizeType(Enum):
    PNG = 'png'
    PDF = 'pdf'
    JSON = 'json'


# endregion

# region utility classes

def except_hook_recv_loop(args):
    if '(_recv_loop)' in args.thread.name \
            and type(args.exc_value) == json.decoder.JSONDecodeError \
            and str(args.exc_value) == "Expecting value: line 1 column 1 (char 0)":
        demisto.debug("Caught a JSONDecodeError exception in _recv_loop, suppressing")
    else:
        raise args.exc_value


class TabLifecycleManager:
    def __init__(self, browser, offline_mode):
        self.browser = browser
        self.offline_mode = offline_mode
        self.tab = None

        demisto.debug(f'TabLifecycleManager, __init__, active tabs len: {len(self.browser.list_tab())}')

    def __enter__(self):
        self.tab = self.browser.new_tab()

        self.tab.start()
        demisto.debug(f"{self.offline_mode=}")
        if self.offline_mode:
            self.tab.Network.emulateNetworkConditions(offline=True, latency=-1, downloadThroughput=-1, uploadThroughput=-1)
        else:
            self.tab.Network.emulateNetworkConditions(offline=False, latency=-1, downloadThroughput=-1, uploadThroughput=-1)

        self.tab.Page.enable()
        demisto.debug(f'TabLifecycleManager, entering tab {self.tab.id}, tabs len: {len(self.browser.list_tab())}')
        return self.tab

    def __exit__(self, exc_type, exc_val, exc_tb):  # pylint: disable=unused-argument
        if exc_type or exc_val or exc_tb:
            demisto.info(f'TabLifecycleManager, __exit__ with exception, {exc_type=}, {exc_val=}, {exc_tb=}')

        if self.tab and self.tab.id:
            tab_id = self.tab.id
            threading.excepthook = except_hook_recv_loop

            try:
                time.sleep(1)  # pylint: disable=E9003
                demisto.debug('TabLifecycleManager, __exit__, disabling page')
                self.tab.Page.disable()
            except Exception as ex:
                demisto.info(f'TabLifecycleManager, failed to disable page due to {ex}')
                pass

            try:
                demisto.debug(
                    f'TabLifecycleManager, __exit__, waiting for tab {tab_id}, active tabs len: {len(self.browser.list_tab())}')
                tab_wait_response = self.tab.wait(timeout=1)
                demisto.debug(f"TabLifecycleManager, __exit__, {tab_wait_response=}")
            except Exception as ex:
                demisto.info(f'TabLifecycleManager, failed to stop tab {tab_id} due to {ex}')
                pass

            try:
                demisto.debug(
                    f'TabLifecycleManager, __exit__, {threading.current_thread().name=}, stopping tab {tab_id}, active tabs len: {len(self.browser.list_tab())}')
                tab_stop_response = self.tab.stop()
                demisto.debug(f"TabLifecycleManager, __exit__, {tab_stop_response=}")
            except json.decoder.JSONDecodeError:
                demisto.info(f'TabLifecycleManager, failed to close tab {tab_id} due to JSONDecodeError')
                pass
            except Exception as ex:
                demisto.info(f'TabLifecycleManager, failed to stop tab {tab_id} due to {ex}')
                pass

            try:
                demisto.debug(
                    f'TabLifecycleManager, __exit__, closing tab {tab_id}, active tabs len: {len(self.browser.list_tab())}')
                self.browser.close_tab(tab_id)
            except json.decoder.JSONDecodeError:
                demisto.info(f'TabLifecycleManager, failed to close tab {tab_id} due to JSONDecodeError')
                pass
            except Exception as ex:
                demisto.info(f'TabLifecycleManager, failed to close tab {tab_id} due to {ex}')
                pass

            demisto.debug(
                f'TabLifecycleManager, __exit__, sleeping, allowing the tab to close, active tabs len: {len(self.browser.list_tab())}')
            time.sleep(1)  # pylint: disable=E9003
            demisto.debug(f'TabLifecycleManager, __exit__, active tabs len: {len(self.browser.list_tab())}')


class PychromeEventHandler:
    request_id = None
    screen_lock = threading.Lock()

    def __init__(self, browser, tab, tab_ready_event):
        self.browser = browser
        self.tab = tab
        self.tab_ready_event = tab_ready_event
        self.start_frame = None

    def frame_started_loading(self, frameId):
        if not self.start_frame:
            self.start_frame = frameId
            demisto.debug(f'Frame started loading: {frameId}')

    def frame_stopped_loading(self, frameId):
        # demisto.debug(f'Frame stopped loading, {frameId=}')
        if self.start_frame == frameId:
            try:
                with self.screen_lock:
                    self.tab.Page.stopLoading()
                    # Activate current tab
                    activation_result = self.browser.activate_tab(self.tab.id)
                    activation_result, operation_time = backoff(activation_result)
                    # if activation_result:
                    #     demisto.debug(f'Tab activated: {activation_result=} after {operation_time} seconds.")')
                    # else:
                    #     demisto.error('Tab not activated. Timeout.')
                    self.tab_ready_event.set()
            except pychrome.exceptions.PyChromeException:
                # demisto.error(f'Error stopping page loading: {self.tab=}, {frameId=}, {e}')
                pass

    def network_data_received(self, requestId, timestamp, dataLength, encodedDataLength):  # pylint: disable=unused-argument
        if requestId and not self.request_id:
            self.request_id = requestId

# endregion


def is_chrome_running(port):
    try:
        processes = subprocess.check_output(['ps', 'auxww'],
                                            stderr=subprocess.STDOUT,
                                            text=True).splitlines()

        chrome_identifiers = ["chrom", "headless", f"--remote-debugging-port={port}"]
        chrome_renderer_identifiers = ["--type=renderer"]
        chrome_processes = [process for process in processes
                            if all(identifier in process for identifier in chrome_identifiers)
                            and not any(identifier in process for identifier in chrome_renderer_identifiers)]

        demisto.debug(f'Detected {len(chrome_processes)} Chrome processes running on port {port}')
        return len(chrome_processes) > 0

    except subprocess.CalledProcessError as e:
        demisto.info(f'Error fetching process list: {e.output}')
        return False
    except Exception as e:
        demisto.info(f'Unexpected error: {e}')
        return False


def is_chrome_running_locally(port):

    browser_url = f"http://{LOCAL_CHROME_HOST}:{port}"
    for i in range(DEFAULT_RETRIES_COUNT):
        try:
            demisto.debug(f"Trying to connect to {browser_url=}, iteration {i+1}/{DEFAULT_RETRIES_COUNT}")
            browser = pychrome.Browser(url=browser_url)

            # Use list_tab to ping the browser and make sure it's available
            browser.list_tab()
            return browser
        except requests.exceptions.ConnectionError as exp:
            exp_str = str(exp)
            connection_refused = 'connection refused'
            if connection_refused in exp_str:
                demisto.debug(f"Failed to connect to Chrome on port {port=} on iteration {i+1}. {connection_refused}")
            else:
                demisto.info(
                    f"Failed to connect to Chrome on port {port=} on iteration {i+1}. ConnectionError, {exp_str=}, {exp=}")

        # mild backoff
        time.sleep(DEFAULT_RETRY_WAIT_IN_SECONDS + i * 2)  # pylint: disable=E9003

    return None


def ensure_chrome_running():  # pragma: no cover
    first_chrome_port = 9201
    ports_list = list(range(first_chrome_port, first_chrome_port + MAX_CHROMES_COUNT))
    demisto.debug(f"Searching for Chrome on these ports: {ports_list}")
    for chrome_port in ports_list:
        chrome_is_running = is_chrome_running(chrome_port)
        browser = is_chrome_running_locally(chrome_port)
        demisto.debug(f"Checking port {chrome_port}: {chrome_is_running=}, {browser}")
        if chrome_is_running and browser:
            # There's a Chrome in that port, and we're connected to it
            demisto.info(f'Connected to Chrome running on port {chrome_port}')
            return browser
        elif chrome_is_running:
            # There's a Chrome in that port, but we couldn't connect to it
            demisto.debug(f"Found Chrome running on port {chrome_port}, but couldn't connect to it")
        else:
            # There's no Chrome in that port
            demisto.debug(f"No Chrome found on port {chrome_port}")
            break
        demisto.debug(f'Could not connect to Chrome on port {chrome_port}')

    if chrome_port == ports_list[-1]:
        demisto.error(f'Max retries ({MAX_CHROMES_COUNT}) reached, could not connect to chrome')
        return None

    demisto.debug(f'Initializing a new Chrome session on port {chrome_port}')
    try:
        process = subprocess.run(['bash', '/start_chrome_headless.sh',
                                 '--port', str(chrome_port),
                                  '--chrome-binary', CHROME_EXE],
                                 text=True, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)

        if process.returncode == 0:
            demisto.debug(f'New Chrome session active on Port {chrome_port}')
            # Allow Chrome to initialize
            time.sleep(DEFAULT_RETRY_WAIT_IN_SECONDS)  # pylint: disable=E9003
            browser = is_chrome_running_locally(chrome_port)
            return browser
        else:
            demisto.debug(f'Chrome did not start successfully on port {chrome_port}. Return code: {process.returncode}')
    except subprocess.SubprocessError as ex:
        demisto.debug(f'Error starting Chrome on port {chrome_port}. Error: {ex}')
    demisto.debug(f'Could not connect to Chrome on port {chrome_port}')

    return None


def setup_tab_event(browser, tab):
    tab_ready_event = Event()
    tab_event_handler = PychromeEventHandler(browser, tab, tab_ready_event)
    tab.Network.dataReceived = tab_event_handler.network_data_received
    tab.Page.frameStartedLoading = tab_event_handler.frame_started_loading
    tab.Page.frameStoppedLoading = tab_event_handler.frame_stopped_loading

    return tab_event_handler, tab_ready_event


def navigate_to_path(browser, tab, path, wait_time, navigation_timeout):  # pragma: no cover
    tab_event_handler, tab_ready_event = setup_tab_event(browser, tab)

    try:
        demisto.debug(f'Starting tab navigation to given path: {path}')

        if navigation_timeout > 0:
            tab.Page.navigate(url=path, _timeout=navigation_timeout)
        else:
            tab.Page.navigate(url=path)

        success_flag = tab_ready_event.wait(navigation_timeout)

        if not success_flag:
            message = f'Timeout of {navigation_timeout} seconds reached while waiting for {path}'
            demisto.error(message)
            return_error(message)

        time.sleep(wait_time)  # pylint: disable=E9003
        demisto.debug(f"navigate_to_path, Navigated to {path=}")
        return tab_event_handler

    except pychrome.exceptions.TimeoutException as ex:
        message = f'Navigation timeout: {ex} thrown while trying to navigate to {path}'
        demisto.error(message)
        return_error(message)
    except pychrome.exceptions.PyChromeException as ex:
        message = f'Exception: {ex} thrown while trying to navigate to {path}'
        demisto.error(message)
        return_error(message)


def backoff(polled_item, wait_time=DEFAULT_WAIT_TIME, polling_interval=DEFAULT_POLLING_INTERVAL):
    operation_time = 0
    while polled_item is None and operation_time < wait_time:
        time.sleep(polling_interval)  # pylint: disable=E9003
        operation_time += polling_interval
    return polled_item, operation_time


def screenshot_image(browser, tab, path, wait_time, navigation_timeout, include_source=False):  # pragma: no cover
    """
    :param include_source: Whether to include the page source in the response
    """
    tab_event_handler = navigate_to_path(browser, tab, path, wait_time, navigation_timeout)

    # Screenshot data
    screenshot_data = tab.Page.captureScreenshot()['data']
    # Make sure that the (asynchronous) screenshot data is available before continuing with execution
    screenshot_data, operation_time = backoff(screenshot_data)
    if screenshot_data:
        demisto.debug(f"Screenshot image available after {operation_time} seconds.")
    else:
        demisto.info(f"Screenshot image not available available after {operation_time} seconds.")

    ret_value = base64.b64decode(screenshot_data)
    if ret_value:
        demisto.debug(f"Captured snapshot, {len(ret_value)=}")
    else:
        demisto.info(f"Empty snapshot, {screenshot_data=}")

    # Page source, if needed
    response_body = None
    demisto.debug(f"{include_source=}")
    if include_source:
        request_id, operation_time = backoff(tab_event_handler.request_id)
        if request_id:
            demisto.debug(f"request_id available after {operation_time} seconds.")
        else:
            demisto.info(f"request_id not available available after {operation_time} seconds.")
        demisto.debug(f"Got {request_id=} after {operation_time} seconds.")
        response_body = tab.Network.getResponseBody(requestId=request_id, _timeout=navigation_timeout)['body']
        response_body, operation_time = backoff(response_body)
        if response_body:
            demisto.debug(f"Response Body available after {operation_time} seconds.")
            demisto.debug(f"{len(response_body)=}")
        else:
            demisto.info(f"Response Body not available available after {operation_time} seconds.")

    return ret_value, response_body


def screenshot_pdf(browser, tab, path, wait_time, navigation_timeout, include_url):  # pragma: no cover
    navigate_to_path(browser, tab, path, wait_time, navigation_timeout)
    header_template = ''
    if include_url:
        header_template = "<span class=url></span>"

    pdf_data = tab.Page.printToPDF(headerTemplate=header_template)['data']
    # Make sure that the (asynchronous) PDF data is available before continuing with execution
    pdf_data, operation_time = backoff(pdf_data)
    if pdf_data:
        demisto.debug(f"PDF Data available after {operation_time} seconds.")
    else:
        demisto.info(f"PDF Data not available available after {operation_time} seconds.")

    ret_value = base64.b64decode(pdf_data)
    return ret_value, None


def rasterize(path: str,
              rasterize_type: RasterizeType = RasterizeType.PNG,
              wait_time: int = DEFAULT_WAIT_TIME,
              offline_mode: bool = False,
              navigation_timeout: int = DEFAULT_PAGE_LOAD_TIME,
              include_url: bool = False,
              width=DEFAULT_WIDTH,
              height=DEFAULT_HEIGHT
              ):
    """
    Capturing a snapshot of a path (url/file), using Chrome Driver
    :param offline_mode: when set to True, will block any outgoing communication
    :param path: file path, or website url
    :param rasterize_type: result type: .png/.pdf
    :param wait_time: time in seconds to wait before taking a screenshot
    :param navigation_timeout: amount of time to wait for a page load to complete before throwing an error
    :param include_url: should the URL be included in the output image/PDF
    :param width: window width
    :param height: window height
    """
    demisto.debug(f"rasterize, {path=}")
    if browser := ensure_chrome_running():
        with TabLifecycleManager(browser, offline_mode) as tab:
            tab.call_method("Emulation.setVisibleSize", width=width, height=height)

            if rasterize_type == RasterizeType.PNG or str(rasterize_type).lower == RasterizeType.PNG.value:
                ret_value, _ = screenshot_image(browser, tab, path, wait_time=wait_time, navigation_timeout=navigation_timeout)
                demisto.debug(f"rasterize, after screenshot_image, {len(ret_value)=}")
                return ret_value, None

            elif rasterize_type == RasterizeType.PDF or str(rasterize_type).lower == RasterizeType.PDF.value:
                ret_value, _ = screenshot_pdf(browser, tab, path, wait_time=wait_time, navigation_timeout=navigation_timeout,
                                              include_url=include_url)
                return ret_value, None

            elif rasterize_type == RasterizeType.JSON or str(rasterize_type).lower == RasterizeType.JSON.value:
                ret_value, response_body = screenshot_image(browser, tab, path, wait_time=wait_time,
                                                            navigation_timeout=navigation_timeout,
                                                            include_source=True)
                return ret_value, response_body
            else:
                message = f'Unsupported rasterization type: {rasterize_type}.'
                demisto.error(message)
                return_error(message)
                return None

    else:
        message = 'Could not use local Chrome for rasterize command'
        demisto.error(message)
        return_error(message)
        return None


def return_err_or_warn(msg):  # pragma: no cover
    return_error(msg) if WITH_ERRORS else return_warning(msg, exit=True)


# region CommandHandlers
def rasterize_image_command():
    args = demisto.args()
    entry_id = args.get('EntryID')
    width, height = get_width_height(demisto.args())

    file_name = args.get('file_name', entry_id)

    file_path = demisto.getFilePath(entry_id).get('path')
    file_name = f'{file_name}.pdf'

    with open(file_path, 'rb') as f:
        output, _ = rasterize(path=f'file://{os.path.realpath(f.name)}', width=width, height=height,
                              rasterize_type=RasterizeType.PDF)
        res = fileResult(filename=file_name, data=output, file_type=entryTypes['entryInfoFile'])
        demisto.results(res)


def rasterize_email_command():  # pragma: no cover
    html_body = demisto.args().get('htmlBody')
    width, height = get_width_height(demisto.args())
    offline = demisto.args().get('offline', 'false') == 'true'
    rasterize_type = RasterizeType(demisto.args().get('type', 'png').lower())
    file_name = demisto.args().get('file_name', 'email')
    navigation_timeout = int(demisto.args().get('max_page_load_time', DEFAULT_PAGE_LOAD_TIME))
    file_name = f'{file_name}.{rasterize_type}'

    with open('htmlBody.html', 'w', encoding='utf-8-sig') as f:
        f.write(f'<html style="background:white";>{html_body}</html>')

    path = f'file://{os.path.realpath(f.name)}'

    output, _ = rasterize(path=path, rasterize_type=rasterize_type, width=width, height=height, offline_mode=offline,
                          navigation_timeout=navigation_timeout)

    res = fileResult(filename=file_name, data=output)

    if rasterize_type == RasterizeType.PNG:
        res['Type'] = entryTypes['image']

    demisto.results(res)


def convert_pdf_to_jpeg(path: str, max_pages: str, password: str):
    """
    Converts a PDF file into a jpeg image
    :param path: file's path
    :param max_pages: max pages to render,
    :param password: PDF password
    :return: A list of stream of combined images
    """
    demisto.debug(f'Loading file at Path: {path}')
    input_pdf = PdfReader(open(path, "rb"), strict=False, password=password)
    pages = len(input_pdf.pages) if max_pages == "*" else min(int(max_pages), len(input_pdf.pages))

    with tempfile.TemporaryDirectory() as output_folder:
        demisto.debug('Converting PDF')
        convert_from_path(
            pdf_path=path,
            fmt='jpeg',
            first_page=1,
            last_page=pages,
            output_folder=output_folder,
            userpw=password,
            output_file='converted_pdf_'
        )
        demisto.debug('Converting PDF - COMPLETED')

        images = []
        for page in sorted(os.listdir(output_folder)):
            if os.path.isfile(os.path.join(output_folder, page)) and 'converted_pdf_' in page:
                images.append(Image.open(os.path.join(output_folder, page)))

        return images


def rasterize_pdf_command():  # pragma: no cover
    entry_id = demisto.args().get('EntryID')
    password = demisto.args().get('pdfPassword')
    max_pages = demisto.args().get('maxPages', PAGES_LIMITATION)
    file_name = demisto.args().get('file_name', 'image')

    file_path = demisto.getFilePath(entry_id).get('path')

    file_name = f'{file_name}.jpeg'

    with open(file_path, 'rb') as f:
        images = convert_pdf_to_jpeg(path=os.path.realpath(f.name), max_pages=max_pages, password=password)
        results = []

        for image in images:
            res = fileResult(filename=file_name, data=image)
            res['Type'] = entryTypes['image']
            results.append(res)

        demisto.results(results)


def rasterize_html_command():
    args = demisto.args()
    entry_id = args.get('EntryID')
    width, height = get_width_height(demisto.args())
    rasterize_type = args.get('type', 'png').lower()

    file_name = args.get('file_name', 'email')
    wait_time = int(args.get('wait_time', 0))

    file_name = f'{file_name}.{rasterize_type}'
    file_path = demisto.getFilePath(entry_id).get('path')
    os.rename(f'./{file_path}', 'file.html')

    output, _ = rasterize(path=f"file://{os.path.realpath('file.html')}", width=width, height=height,
                          rasterize_type=rasterize_type, wait_time=wait_time)

    res = fileResult(filename=file_name, data=output)
    if rasterize_type == 'png':
        res['Type'] = entryTypes['image']
    return_results(res)


def module_test():  # pragma: no cover
    # setting up a mock email file
    with tempfile.NamedTemporaryFile('w+') as test_file:
        test_file.write('<html><head><meta http-equiv=\"Content-Type\" content=\"text/html;charset=utf-8\">'
                        '</head><body><br>---------- TEST FILE ----------<br></body></html>')
        test_file.flush()
        file_path = f'file://{os.path.realpath(test_file.name)}'

        # rasterizing the file
        rasterize(path=file_path)

    demisto.results('ok')


def rasterize_command():  # pragma: no cover
    url = demisto.getArg('url')
    demisto.debug(f"rasterize_command {url=}")
    width, height = get_width_height(demisto.args())
    rasterize_type = RasterizeType(demisto.args().get('type', 'png').lower())
    wait_time = int(demisto.args().get('wait_time', 0))
    navigation_timeout = int(demisto.args().get('max_page_load_time', DEFAULT_PAGE_LOAD_TIME))
    file_name = demisto.args().get('file_name', 'url')
    include_url = argToBoolean(demisto.args().get('include_url', False))

    if not (url.startswith('http')):
        url = f'http://{url}'
    file_name = f'{file_name}.{"pdf" if rasterize_type == RasterizeType.PDF else "png"}'  # type: ignore

    rasterize_output, response_body = rasterize(path=url, rasterize_type=rasterize_type, wait_time=wait_time,
                                                navigation_timeout=navigation_timeout, include_url=include_url)
    demisto.debug(f"rasterize_command response, {rasterize_type=}, {len(rasterize_output)=}")

    if rasterize_type == RasterizeType.JSON or str(rasterize_type).lower == RasterizeType.JSON.value:
        demisto.info("JSON output needed")
        output = {'image_b64': base64.b64encode(rasterize_output).decode('utf8'),
                  'html': response_body, 'current_url': url}
        demisto.results(CommandResults(raw_response=output, readable_output="Successfully rasterize url: " + url))
    else:
        res = fileResult(filename=file_name, data=rasterize_output)
        if rasterize_type == RasterizeType.PNG or str(rasterize_type).lower == RasterizeType.PNG.value:
            res['Type'] = entryTypes['image']
        demisto.debug(f"rasterize_command {res.keys()=}")

        demisto.results(res)

# endregion


def get_width_height(args: dict):
    """
    Get commomn args.
    :param args: dict to get args from
    :return: width, height, rasterize mode
    """
    width = int(args.get('width', f"{DEFAULT_WIDTH} px").rstrip('px'))
    height = int(args.get('height', f"{DEFAULT_HEIGHT} px").rstrip('px'))

    # Check that the width and height meet the safeguard limit
    width = min(width, MAX_FULLSCREEN_WIDTH)
    height = min(height, MAX_FULLSCREEN_HEIGHT)

    return width, height


def main():  # pragma: no cover
    demisto.debug(f"main, {demisto.command()=}")
    try:
        if demisto.command() == 'test-module':
            module_test()

        elif demisto.command() == 'rasterize-image':
            rasterize_image_command()

        elif demisto.command() == 'rasterize-email':
            rasterize_email_command()

        elif demisto.command() == 'rasterize-pdf':
            rasterize_pdf_command()

        elif demisto.command() == 'rasterize-html':
            rasterize_html_command()

        elif demisto.command() == 'rasterize':
            rasterize_command()

        else:
            return_error('Unrecognized command')

    except Exception as ex:
        return_err_or_warn(f'Unexpected exception: {ex}\nTrace:{traceback.format_exc()}')


if __name__ in ["__builtin__", "builtins", '__main__']:
    main()
