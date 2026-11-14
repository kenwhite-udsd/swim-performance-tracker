"""swim race tracker."""

from dataclasses import dataclass, field
from drafter import *


# Global constants are allowed by the project requirements.
EVENTS = ["50 Free", "100 Free", "200 Free", "100 Breast", "200 IM"]


@dataclass
class RaceResult:
    """One race time entered by the swimmer."""
    event: str
    time_seconds: float
    date: str


@dataclass
class State:
    """Information that the site keeps as the swimmer visits pages."""
    race_results: list[RaceResult] = field(default_factory=list)
    goal_times: dict[str, float] = field(default_factory=dict)
    selected_event: str = "100 Breast"
    status_message: str = "Welcome! Add a race to start tracking progress."


def results_for_event(state: State, event: str) -> list[RaceResult]:
    """Return the race results for one event."""
    matching_results = []
    for result in state.race_results:
        if result.event == event:
            matching_results.append(result)
    return matching_results


def best_result(results: list[RaceResult]) -> RaceResult | None:
    """Return the fastest result, or None when the list is empty."""
    if len(results) == 0:
        return None
    fastest = results[0]
    for result in results:
        if result.time_seconds < fastest.time_seconds:
            fastest = result
    return fastest


def navigation(state: State) -> list:
    """Create button navigation to the main pages."""
    return [
        Button("Dashboard", "index"),
        Button("Add Race", "add_race_page"),
        Button("Results", "results_page",
               [("event", state.selected_event)]),
        Button("Personal Bests", "personal_bests_page"),
        Button("Goals", "goals_page"),
        Button("Progress", "progress_page",
               [("event", state.selected_event)])
    ]


def show_message(state: State) -> list:
    """Show the latest action message."""
    return [Paragraph(state.status_message)]


@route("index")
def home_page(state: State, event: str = "", time_seconds: float = 0.0,
              race_date: str = "", goal_seconds: float = 0.0) -> Page:
    """Show the dashboard and links to the tracker pages."""
    content = [
        Header("Swim Performance Tracker"),
        Paragraph("Record race times, find personal bests, and track goals."),
    ]
    content.extend(show_message(state))
    content.extend(navigation(state))
    return Page(state, content)


@route
def add_race_page(state: State, event: str = "", time_seconds: float = 0.0,
                  race_date: str = "", goal_seconds: float = 0.0) -> Page:
    """Show the form for entering a race result."""
    content = [Header("Add a Race"), Paragraph("Choose an event and enter your time in seconds."),
               "Event:", SelectBox("event", EVENTS, state.selected_event),
               "Race time in seconds:", TextBox("time_seconds", 0.0, "number"),
               "Race date (YYYY-MM-DD):", TextBox("race_date"),
               Button("Submit Race", "save_race")]
    content.extend(show_message(state))
    content.extend(navigation(state))
    return Page(state, content)


@route
def save_race(state: State, event: str, time_seconds: float,
              race_date: str, goal_seconds: float = 0.0) -> Page:
    """Validate and save a race, then show the results page."""
    state.selected_event = event
    if time_seconds <= 0 or race_date.strip() == "":
        state.status_message = "Enter a time above zero and a race date."
        return add_race_page(state)
    state.race_results.append(RaceResult(event, time_seconds, race_date))
    state.status_message = "Race saved."
    return results_page(state, event)


@route
def results_page(state: State, event: str, time_seconds: float = 0.0,
                 race_date: str = "", goal_seconds: float = 0.0) -> Page:
    """Display race results for the selected event."""
    # Drafter can carry fields from the previous form into a page link.
    # These optional parameters accept those values; they are not used here.
    state.selected_event = event
    content = [Header("Race Results"), "Choose an event:",
               SelectBox("event", EVENTS, event),
               Button("Show Results", "results_page")]
    matching_results = results_for_event(state, event)
    if len(matching_results) == 0:
        content.append(Paragraph("No race results for this event yet."))
    else:
        for result in matching_results:
            content.append(Paragraph(
                str(result.time_seconds) + " seconds - " + result.date))
    content.extend(show_message(state))
    content.extend(navigation(state))
    return Page(state, content)


@route
def personal_bests_page(state: State, event: str = "",
                        time_seconds: float = 0.0, race_date: str = "",
                        goal_seconds: float = 0.0) -> Page:
    """Display the fastest recorded time for each event."""
    content: list = [Header("Personal Bests")]
    for event in EVENTS:
        fastest = best_result(results_for_event(state, event))
        if fastest is None:
            content.append(Paragraph(event + ": no times recorded yet."))
        else:
            content.append(Paragraph(
                event + ": " + str(fastest.time_seconds) + " seconds"))
    content.extend(navigation(state))
    return Page(state, content)


@route
def goals_page(state: State, event: str = "", time_seconds: float = 0.0,
               race_date: str = "", goal_seconds: float = 0.0) -> Page:
    """Show current goals and a form to add or update a goal."""
    # Ignore race-entry fields that may be carried into this page by Drafter.
    if event in EVENTS:
        state.selected_event = event
    event = state.selected_event
    current_goal = state.goal_times.get(event, 0.0)
    content = [Header("Goals"), "Choose an event:",
               SelectBox("event", EVENTS, event),
               "Goal time in seconds:",
               TextBox("goal_seconds", current_goal, "number"),
               Button("Save Goal", "save_goal")]
    for goal_event in state.goal_times:
        content.append(Paragraph(
            goal_event + " goal: " + str(state.goal_times[goal_event]) + " seconds"))
    content.extend(show_message(state))
    content.extend(navigation(state))
    return Page(state, content)


@route
def save_goal(state: State, event: str, goal_seconds: float,
              time_seconds: float = 0.0, race_date: str = "") -> Page:
    """Save a positive goal time for the selected event."""
    state.selected_event = event
    if goal_seconds <= 0:
        state.status_message = "Enter a goal time above zero."
    else:
        state.goal_times[event] = goal_seconds
        state.status_message = "Goal saved."
    return goals_page(state)


@route
def progress_page(state: State, event: str = "", time_seconds: float = 0.0,
                  race_date: str = "", goal_seconds: float = 0.0) -> Page:
    """Compare the first time, current best, and goal for an event."""
    if event == "":
        event = state.selected_event
    state.selected_event = event
    matching_results = results_for_event(state, event)
    content = [Header("Progress"), "Choose an event:",
               SelectBox("event", EVENTS, event),
               Button("Show Progress", "progress_page")]
    if len(matching_results) == 0:
        content.append(Paragraph("Add a race result to see progress."))
    else:
        first_time = matching_results[0].time_seconds
        fastest = best_result(matching_results)
        if fastest is None:
            content.append(Paragraph("Could not calculate a best time."))
        else:
            content.append(Paragraph("First entered time: " + str(first_time) + " seconds"))
            content.append(Paragraph("Current best: " + str(fastest.time_seconds) + " seconds"))
            improvement = first_time - fastest.time_seconds
            content.append(Paragraph("Improvement: " + str(round(improvement, 2)) + " seconds"))
            if event in state.goal_times:
                goal = state.goal_times[event]
                content.append(Paragraph("Goal time: " + str(goal) + " seconds"))
                if fastest.time_seconds <= goal:
                    content.append(Paragraph("Goal reached!"))
                else:
                    content.append(Paragraph(
                        str(round(fastest.time_seconds - goal, 2)) + " seconds to goal."))
            else:
                content.append(Paragraph("Set a goal to track it here."))
    content.extend(navigation(state))
    return Page(state, content)


set_website_title("Swim Performance Tracker")
set_site_information(
    author="Ken White",
    description=(
        "Record swim race times, compare personal bests, and track goals."
    ),
    sources="No external images or data are used.",
    planning=[],
    links=[
        "https://github.com/kenwhite-udsd/swim-performance-tracker"
    ],
)
hide_debug_information()
set_website_framed(False)

start_server(State())

