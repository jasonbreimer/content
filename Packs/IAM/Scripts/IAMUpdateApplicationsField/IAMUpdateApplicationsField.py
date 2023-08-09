import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401


def main():
    args = demisto.args()

    applications = args.get("applications")
    if not applications:
        applications = []
    else:
        try:
            applications = json.loads(applications)
        except json.decoder.JSONDecodeError:
            raise ValueError(
                "applications input is not JSON serializable, please check: "
                + applications
            )

    instances = argToList(args.get("instance_name"))
    brands = argToList(args.get("brand"))
    user_ids = argToList(args.get("user_id"))
    statuses = argToList(args.get("active"))

    user_apps_data = []

    if (
        len(instances) != len(brands)
        or len(instances) != len(user_ids)
        or len(instances) != len(statuses)
    ):
        raise ValueError(
            "Make sure the instance_name, brand, user_id and active arguments have the same length."
        )

    for instance_name, brand, user_id, status in zip(
        instances, brands, user_ids, statuses
    ):
        user_apps_data.append(
            {
                "Instance Name": instance_name,
                "Brand": brand,
                "User ID": user_id,
                "Active": status,
            }
        )

    applications = [
        app for app in applications if app.get("Instance Name") not in instances
    ]
    applications.extend(user_apps_data)

    applications_json = json.dumps(applications)

    context = {"UserApplications": applications_json}

    entry = {
        "Type": entryTypes["note"],
        "Contents": applications,
        "ContentsFormat": formats["json"],
        "ReadableContentsFormat": formats["markdown"],
        "HumanReadable": tableToMarkdown("Updated User Applications", applications),
        "EntryContext": context,
    }
    demisto.results(entry)


if __name__ in ["__main__", "builtin", "builtins"]:
    main()
