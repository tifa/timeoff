# timeoff 🏝

Do your PTO hours keep expiring? Are you saving up for a big trip? Do you have
a flex vacation policy? Track your hours accrued and set goals and
reminders to take a break!

```console
$ timeoff list

  |    o               ,---.,---.
  |--- .,-.-.,---.,---.|__. |__.
  |    || | ||---'|   ||    |
  `---'`` ' '`---'`---'`    `

  Current schedule: SemiMonthly
                    4 hours on the 1st and 15th of the month
╭────────────┬───────┬──────────┬─────────┬─────────────╮
│   Start    │  End  │   Type   │   Hours │   Remaining │
├────────────┼───────┼──────────┼─────────┼─────────────┤
│            │       │ Initial  │     100 │         100 │
│ 2023-05-12 │   -   │ Vacation │      -8 │          92 │
│ 2023-05-15 │   -   │ Accrued  │       4 │          96 │
╰────────────┴───────┴──────────┴─────────┴─────────────╯
```

## Features

- Automaticaly updates PTO hours over time.
- Define schedules to set accrued PTO rates.
- View the remaining hours of PTO available to you.

## Installation

To install ``timeoff``:

```console
$ pip install timeoff
```

Documentation is in the works! Please run the `-h` help flag in the meantime. The interactive prompts will guide you through further instructions.

```console
$ timeoff -h
usage: timeoff [-h] {add,list,rm,settings} ...

Timeoff CLI

positional arguments:
  {add,list,rm,settings}
                        sub-command help
    add                 Add an absence
    list                List absences
    rm                  Remove an absence
    settings            Manage settings

optional arguments:
  -h, --help            show this help message and exit
```
