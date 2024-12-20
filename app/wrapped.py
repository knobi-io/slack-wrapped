import json
import random

title_choices = [
    "Hey <@USERID>! Here's your Slack Wrapped for 2024:",
    "Here it is! Slack Wrapped for <@USERID>!",
    "Hope you enjoyed the 2024, <@USERID>! Here's your Slack Wrapped:",
    "Slack Wrapped for <@USERID>! Check it out!",
    "And the Slack Wrapped for <@USERID> is here!",
    "Okay, let's see what you did in 2024, <@USERID>!",
    "Slack Wrapped for <@USERID>! Drumroll please!",
]

closing_line_choices = [
    "Hope you enjoyed your 2024, <@USERID>! Here's to an even better 2025!",
    "That's all for now, <@USERID>! Here's to a great 2025!",
    "And that's a wrap! Hope you had a great 2024, <@USERID>!",
    "That's all for now, <@USERID>! Here's to a great 2025!",
    "What a year, <@USERID>! Can't wait to see what you do in 2025!",
    "And it all went by so fast! Hope you had a great 2024, <@USERID>!",
    "See you next year, <@USERID>!"
]

def emoji_for(percent):
    emoji_thresholds = [
        (2, ':heart_on_fire:'),
        (5, ':fire:'),
        (10, ':star:'),
        (25, ':sunglasses:'),
        (50, ':grin:')
    ]
    for threshold, emoji in emoji_thresholds:
        if percent <= threshold:
            return emoji
    return ':smile:'

def buddy_line_for(count):
    buddy_lines = [
        (45, "must be bound by fate"),
        (30, "were pals"),
        (15, "must get along well"),
        (10, "bumped into eachother a lot"),
    ]

    for threshold, line in buddy_lines:
        if count >= threshold:
            return line

    return "crossed paths"

def get_wrapped(user_id):
    stats_file = open('final_stats.json', 'r')
    stats = json.load(stats_file)
    stats_file.close()

    if user_id not in stats:
        return None
    
    stats = stats[user_id]

    title = random.choice(title_choices)
    title = title.replace('<@USERID>', f'<@{user_id}>')

    message = f"{title}\n\n"
    message += f"You were in the top *{stats['threads_started_percentile']}%* of conversation starters, creating *{stats['threads_started']} threads*. {emoji_for(stats['threads_started_percentile'])} \n"
    message += f"You replied to other members *{stats['replies']} times*, putting you in the top *{stats['replies_percentile']}%* of repliers. {emoji_for(stats['replies_percentile'])} \n"

    if stats['most_reactions_received'] != None:
        if stats['most_reactions_received'][0][0] == stats['most_used_reaction'][0][0]:
            message += f"\nYou're posts received a :{stats['most_reactions_received'][0][0]}: more than any other reaction, and you gave it right back, using it *{stats['most_used_reaction'][0][1]} times*!\n"
        else:
            message += f"\nYou're posts received a :{stats['most_reactions_received'][0][0]}: more than any other reaction.\n"
            if stats['most_used_reaction'][0][0] != None:
                message += f"But you preferred :{stats['most_used_reaction'][0][0]}: and used it *{stats['most_used_reaction'][0][1]} times*.\n"

    message += f"\nYour favorite channels to post in were: "
    for channel in stats['top_channels'][:3]:
        message += f"\n- #{channel[0]} ({channel[1]} posts)"
    
    if stats['top_co_posters'][0][1] >= 5:
        message += f"\n\nYou and <@{stats['top_co_posters'][0][0]}> {buddy_line_for(stats['top_co_posters'][0][1])}, posting in the same thread *{stats['top_co_posters'][0][1]} times*.\n"

    message += f"\nAs far as engagement goes, your threads received a total of *{stats['engagement_received']} reactions & replies*, putting you in the top *{stats['engagement_received_percentile']}%*. {emoji_for(stats['engagement_received_percentile'])} \n"
    
    message += f"\n{random.choice(closing_line_choices).replace('<@USERID>', f'<@{user_id}>')}\nThanks for being one of us! :sparkles:"
    return message