import argparse
from datetime import datetime, timedelta
from pathlib import Path

from tabulate import tabulate

from timeoff.config import DATA_DIR, SCHEDULES
from timeoff.model.entry import Absence, Accrued
from timeoff.model.policy import Policy
from timeoff.model.setting import Setting
from timeoff.prompt import date_validator, float_validator, prompt
from timeoff.update import update_pto


def header(func):
    def wrapper():
        """Prompt header. Source: https://ascii.today"""
        print("")
        print("  |    o               ,---.,---.")
        print("  |--- .,-.-.,---.,---.|__. |__.")
        print("  |    || | ||---'|   ||    |")
        print("  `---'`` ' '`---'`---'`    `")
        print("")
        func()

    return wrapper


def refresh_pto(func):
    def wrapper():
        if not Path(DATA_DIR).is_dir():
            print("Please initialize by running `timeoff settings`.")
        else:
            update_pto()
            func()

    return wrapper


def show_table():
    def concat_entries(entries):
        if entries is None or len(entries) == 0:
            return []

        entries.sort(key=lambda x: x.date)
        it = iter(entries)
        current_entry = next(it, None)
        if current_entry is None:
            return []
        
        start_date = current_entry.date
        end_date = start_date
        rate = (
            current_entry.rate
            if type(current_entry) == Accrued
            else (current_entry.rate * -1)
        )

        results = []
        for next_entry in it:
            if type(current_entry) == type(next_entry) \
                and current_entry.date + timedelta(days=1) == next_entry.date \
                and current_entry.rate == next_entry.rate:
                end_date = next_entry.date
            else:
                results.append((start_date, end_date, rate))
                start_date = next_entry.date
                end_date = start_date
                rate = (
                    next_entry.rate
                    if type(next_entry) == Accrued
                    else (next_entry.rate * -1)
                )
            current_entry = next_entry

        results.append((start_date, end_date, rate))
        return results

    accrued_pto = list(Accrued.get().values())
    absences = list(Absence.get().values())
    entries = accrued_pto + absences
    entries.sort(key=lambda x: x.date)
    entries = concat_entries(entries)

    settings = Setting.get()

    headers = ["Start", "End", "Type", "Hours", "Remaining"]

    formatted = []
    remaining = settings.starting_balance
    for entry in entries:
        num_days = (entry[1] - entry[0]).days + 1
        total_hours = entry[2] * num_days
        remaining += total_hours
        formatted.append(
            [
                entry[0],
                "-" if entry[0] == entry[1] else entry[1],
                "Accrued" if entry[2] > 0 else "Vacation",
                total_hours,
                remaining,
            ],
        )
    formatted.insert(
        0, ["", "", "Initial", settings.starting_balance, settings.starting_balance],
    )

    policies = Policy.get()
    latest_policy_date = list(policies.keys())[-1]
    policy = policies[latest_policy_date]

    print(f"  Current schedule: {policy.schedule.__class__.__name__}")
    print(f"                    {int(policy.rate)} hours on {policy.schedule.description()}")
    print(
        tabulate(
            formatted,
            headers=headers,
            tablefmt="rounded_outline",
            colalign=("center", "center", "center", "right", "right"),
        ),
    )

@header
@refresh_pto
def add_prompt():
    current_date = datetime.now().date()
    starting_date = Setting.get().starting_date

    questions = [
        {
            "type": "input",
            "name": "start_date",
            "message": "Start date (YYYY-MM-DD)",
            "default": str(current_date),
            "validate": date_validator(lambda val: val >= starting_date
                                       or f"Please enter a date on/after the starting date {starting_date}"),
            "filter": lambda val: datetime.strptime(val, "%Y-%m-%d").date(),
        },
    ]
    answers = prompt(questions)
    questions = [
        {
            "type": "input",
            "name": "end_date",
            "message": "End date (YYYY-MM-DD)",
            "default": str(answers["start_date"]),
            "validate": date_validator(lambda val: val >= answers["start_date"]
                                        or f"Please enter a date on/after the start date {answers['start_date']}"),
            "filter": lambda val: datetime.strptime(val, "%Y-%m-%d").date(),
        },
        {
            "type": "input",
            "name": "rate",
            "message": "Hours per day",
            "default": "8",
            "validate": float_validator(lambda val: val > 0
                                         or "Please enter a number greater than 0"),
            "filter": lambda val: float(val),
        },
    ]
    answers.update(prompt(questions))

    current_date = answers["start_date"]
    while current_date <= answers["end_date"]:
        Absence(current_date, answers["rate"]).save()
        current_date += timedelta(days=1)

    print("Saved!")
    show_table()


@header
@refresh_pto
def list_prompt():
    show_table()


@header
@refresh_pto
def rm_prompt():
    questions = [
        {
            "type": "input",
            "name": "date",
            "message": "Date to remove (YYYY-MM-DD)",
            "validate": date_validator(lambda _: True),
            "filter": lambda val: datetime.strptime(val, "%Y-%m-%d").date(),
        },
    ]
    answers = prompt(questions)
    Absence.rm(answers["date"])
    print("Removed!")
    show_table()


@header
def settings_prompt():
    if Path(DATA_DIR).is_dir():
        print("Functionality to update settings and policies TBD.")
        print("If you want to start all over, delete the directory: ~/.timeoff")
        print("This will wipe out all of your data! :(")
        return

    questions = [
        {
            "type": "input",
            "name": "starting_balance",
            "message": "Starting balance (hours)",
            "default": "0",
            "validate": float_validator(lambda val: val >= 0
                                         or "Please enter a number greater than or equal to 0"),
            "filter": lambda val: float(val),
        },
        {
            "type": "input",
            "name": "starting_date",
            "message": "Starting date (YYYY-MM-DD)",
            "default": str(datetime.now().date()),
            "validate": date_validator(lambda val: val <= datetime.now().date()
                                        or "Please enter a date that is on or before today"),
            "filter": lambda val: datetime.strptime(val, "%Y-%m-%d").date(),
        },
        {
            "type": "list",
            "name": "schedule",
            "message": "Schedule",
            "choices": SCHEDULES.keys(),
            "filter": lambda val: SCHEDULES[val],
        },
    ]
    answers = prompt(questions)

    schedule_args = answers["schedule"].setup_prompt()

    questions = [
        {
            "type": "input",
            "name": "rate",
            "message": "Rate (hours per period)",
            "default": "4",
            "validate": float_validator(lambda val: val > 0
                                         or "Please enter a number greater than 0"),
            "filter": lambda val: float(val),
        },
    ]
    rate_answers = prompt(questions)
    answers.update(rate_answers)

    Setting(answers["starting_balance"], answers["starting_date"]).save()
    Policy(answers["starting_date"], answers["schedule"].__name__, schedule_args, answers["rate"]).save()
    print("Saved!")

    update_pto()
    show_table()


def main():
    parser = argparse.ArgumentParser(description="Timeoff CLI")
    subparsers = parser.add_subparsers(help="sub-command help")

    # Subpaser for the 'add' command
    parser_add = subparsers.add_parser("add", help="Add an absence")
    parser_add.set_defaults(func=add_prompt)

    # Subparser for the 'list' command
    parser_list = subparsers.add_parser("list", help="List absences")
    parser_list.set_defaults(func=list_prompt)

    # Subparser for the 'rm' command
    parser_rm = subparsers.add_parser("rm", help="Remove an absence")
    parser_rm.set_defaults(func=rm_prompt)

    # Subparser for the 'settings' command
    parser_settings = subparsers.add_parser("settings", help="Manage settings")
    parser_settings.set_defaults(func=settings_prompt)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
