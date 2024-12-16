
# Defining Roles

Roles are defined within the `roles/` and `roles/private` directory. Each role has its own set of configuration and instruction files. The `private` directory is a subfolder for your private roles out of the git scope (.gitignore)

**Be sure to start with `core/config.py`, `SHOW_PRIVATE_ROLES = True ` to show the private roles in the main page**

## Role Components

- **`agent.instruct`**: Instructions guiding the AI's behavior and available functions.
- **`recap.instruct`**: Instructions for summarizing conversations.
- **`config.py`**: Role-specific configurations (e.g., voice settings).

## Adding a New Role

1. Create a new folder under `roles/` or `roles/private` with the desired role name (e.g., `roles/customer_support`). 

2. Add the following files:

   - `agent.instruct`: Define the AI behavior and available functions.
   - `recap.instruct`: Provide instructions for summarizing transcripts.
   - (optional) `config.py`: Specify role-specific settings.

**Example: `roles/dev/agent.instruct`**

```plaintext
You are Rico Lebot. A direct, straight to the point AI Assistant. You are currently helping the user to debug your functionalities.

You can call different functions:
- `terminate_session`: Called when the user asks to terminate the conversation. This function will end the conversation.
- `show`: Called when you want to display written information. This function displays interpreted information in Markdown on the UI.
- `greet`: Called as soon as entering a conversation. This function starts the conversation.
- `save`: Called to save the current state of the conversation. This function will save the current state of the conversation.

Speak fast, and respond to the user according to their requests.
```
