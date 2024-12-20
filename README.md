# slack-wrapped
Create a "Wrapped" /command for your Slack Workspace

Start by creating a manual export of your slack history public channels for time range you want to "wrap".
Place that zip file in the "prep" directory.
Edit the zip_file_path in prep_stats.py
- Optional: fill in any excluded user IDs

Run prep_stats.py
- This will create a "final_stats.json" file

Copy "final_stats.json" to the app directory.
- Publish the contents of the app directory to an Azure Function App (using python 3.9)
- Your function app will have a single function named "slack_command"
- You can use the URL for that function as the endpoint for a slash command for slack bot
- It will respond with an ephemeral message (only visible the user) displaying their stats.

(Note: Several of the messages in app/wrapped.py reference 2024/2025 - modify them as needed.)

## Got other cool things you'd like to do with your slack workspace?
Knobi builds custom tools for community platforms like Slack, Discord and more. 
Check us out at Knobi.io
🎈