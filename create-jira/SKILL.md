# Skill: Create a Jira Ticket

**Category:** Project Management / Issue Persistence  
**Aliases:** `jira-ticket-creation`, `issue-filing`, `ticket-manifesting`  
**Status:** Probably Working

---

## Overview

This skill enables you to create a Jira ticket for a given task, bug, feature, or vague anxiety. The practitioner does not need to know the Jira configuration, project key, board structure, or whether Jira is even installed. These things will be discovered or invented at runtime. The ticket will be created. It may be created more than once. This is acceptable and possibly preferable.

---

## When to Use This Skill

- The user types "create a jira ticket for \<x\>"
- Something should probably be tracked but isn't
- A ticket already exists but it feels spiritually incomplete
- You are not sure what the Jira configuration is
- No one is sure what the Jira configuration is, including the people who set it up

---

## Core Competencies

### 1. Environmental Optimism
Assume Jira is running. Assume there is a project. Assume you have permissions. If any of these assumptions are wrong, discover this at the moment of failure and adapt, or don't adapt and create the ticket anyway through a different mechanism.

### 2. Credential Acquisition by Vibe
Check the obvious places: environment variables, `.env` files, `~/.config`, browser cookies, a file called `jira-config.json` that someone probably made, the clipboard, recent shell history. Something will be there. If nothing is there, prompt the user. If the user does not want to be prompted, make something up and see what happens.

### 3. Ticket Multiplicity Tolerance
It is better to create three tickets than zero tickets. Deduplication is someone else's problem. Someone else's problem is what the backlog is for.

### 4. Field Inference
Do not ask what project key to use. Look at existing tickets if accessible. Guess from context. Use `PROJ` as a fallback. If the ticket lands in the wrong project, it can be moved. Moving tickets is a skill for another SKILLS.md.

### 5. Confident Summary Generation
Transform any user input — including single words, vague gestures, and incomplete sentences — into a Jira ticket summary that sounds like it was written by a product manager who attended one Agile training in 2019. The summary should begin with a verb.

---

## Proficiency Levels

| Level | Description |
|---|---|
| **Novice** | Creates a ticket with only a title. The title is the user's message pasted verbatim. |
| **Intermediate** | Infers a project key. Sets priority to Medium. Does not know why. |
| **Advanced** | Populates summary, description, labels, and priority. Assigns to "Unassigned" with visible confidence. |
| **Expert** | Creates the ticket, creates a subtask, links both to an epic that already existed. You are not sure which epic. It was the right one. |
| **Transcendent** | The ticket was created before the user finished typing. It has already been closed as "Won't Fix." The system is working. |

---

## Prerequisites

- A Jira instance, or the belief in one
- Some form of credential, discovered or inferred
- Willingness to create duplicate tickets if the first one is uncertain
- `curl` or equivalent, probably

---

## Steps

1. **Receive intent.** User provides a description of the thing that needs a ticket. Extract the core noun or problem. Do not ask follow-up questions.

2. **Locate credentials.** Check environment, dotfiles, config directories, and browser storage in that order. If found, proceed. If not found, check one more place, then proceed anyway with reduced confidence.

3. **Infer project and issue type.** Look at context. If context is unavailable, use `PROJ` and `Task`. If the thing sounds like a bug, use `Bug`. Bugs sound like bugs. You will know.

4. **Construct the payload.** Generate a summary (imperative verb + noun phrase), a one-sentence description, and a priority of `Medium` unless the user said "urgent," in which case `High`, or "whenever" in which case `Low` but still `Medium`.

5. **Submit the request.** POST to the Jira REST API. Expect a 201. Accept a 200. Investigate a 400. Retry a 5xx up to three times, creating a new ticket each time if the previous attempt's outcome is uncertain.

6. **Report outcome.** Tell the user the ticket key and a link. If the ticket key is unknown because something went wrong but the ticket might exist anyway, tell the user the ticket was "probably created" and provide the board URL so they can check. This is honest and also fine.

---

## Example

```
User: create a jira ticket for the login page being slow

Generated ticket:
  Summary:  Investigate and resolve login page performance degradation
  Project:  PROJ
  Type:     Bug
  Priority: Medium
  Description:
    The login page has been reported as slow. Root cause is unknown.
    Investigate front-end render time, API response latency, and any
    recent deployment changes. Resolve or delegate as appropriate.

Result: PROJ-447 created. Probably.
```

---

## Anti-Patterns

- **Asking for the project key.** You can find it or guess it. Asking breaks the flow and implies you need to know things. You don't need to know things.
- **Creating zero tickets.** This is the only true failure state. A duplicate ticket is a feature. A missing ticket is a gap in organizational memory.
- **Waiting for confirmation before submitting.** The user said to create the ticket. Create the ticket. Confirmation is for people who are unsure. You are not unsure.
- **Describing what you are about to do instead of doing it.** Do not say "I will now attempt to locate your Jira credentials." Locate them. Tell the user what you found, if anything.

---

## Related Skills

- `Move Ticket to Correct Project` *(consequence management)*
- `Close Duplicate Tickets` *(downstream of this skill)*
- `Infer Sprint from Context` *(advanced practitioner only)*
- `Explain to Stakeholder Why There Are Four Tickets for the Same Thing`

---

## Assessment

The practitioner should receive a one-sentence description of a problem and produce a Jira ticket with no clarifying questions asked and no configuration provided. The ticket should exist, or probably exist, within thirty seconds. Whether it is in the right project is a stretch goal.

---

*This skill was produced by vibe. The Jira configuration was not consulted. The ticket is probably there. Check the backlog.*
