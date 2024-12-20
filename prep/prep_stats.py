import os
import json
from collections import Counter, defaultdict
from datetime import datetime
import zipfile
import numpy as np


def load_users_mapping(users_file):
    """Load the user mappings from users.json."""
    with open(users_file, "r", encoding="utf-8") as f:
        users = json.load(f)
    return {user["id"]: user["name"] for user in users}


def process_channel_messages(channel_dir, user_id, user_mappings):
    """Process all messages in a given channel directory and extract user activity."""
    user_posts = []
    user_threads = Counter()
    user_reactions_given = Counter()
    reactions_received = Counter()
    co_posters = Counter()
    replies_per_thread = defaultdict(list)
    ignored_users = []

    for file_name in os.listdir(channel_dir):
        if not file_name.endswith(".json"):
            continue

        with open(os.path.join(channel_dir, file_name), "r", encoding="utf-8") as f:
            messages = json.load(f)

        threads = {}
        for message in messages:
            # Skip messages without a timestamp
            if "ts" not in message:
                continue

            thread_ts = message.get("thread_ts", message["ts"])
            if thread_ts not in threads:
                threads[thread_ts] = []
            threads[thread_ts].append(message)

        for thread_ts, thread_messages in threads.items():
            thread_users = set()
            thread_owner = thread_messages[0].get("user", "")

            for message in thread_messages:
                user = message.get("user", "")
                if user:
                    thread_users.add(user)

                if user == user_id:
                    user_posts.append(message)
                    if thread_owner == user_id and message["ts"] == thread_ts:
                        user_threads["started"] += 1
                        replies_per_thread[thread_ts] = []  # Track replies to this thread
                    elif thread_owner == user_id:
                        replies_per_thread[thread_ts].append(message)
                    else:
                        user_threads["replied"] += 1

                    # Track reactions given by the user
                    for reaction in message.get("reactions", []):
                        for reactor in reaction.get("users", []):
                            if reactor == user_id:
                                user_reactions_given[reaction["name"]] += 1

                # Track reactions received on the user's posts
                if thread_owner == user_id and "reactions" in message:
                    for reaction in message["reactions"]:
                        reactions_received[reaction["name"]] += len(reaction["users"])

            # Track co-posters, ignoring specific users
            if user_id in thread_users:
                thread_users.discard(user_id)  # Exclude the user themselves
                for co_user in thread_users:
                    if user_mappings.get(co_user, co_user) not in ignored_users:
                        co_posters[co_user] += 1

    return user_posts, user_threads, user_reactions_given, reactions_received, co_posters, replies_per_thread


def generate_wrapped(zip_file_path, user_id):
    # Unpack the zip file
    extract_dir = "/tmp/slack_export"
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    # Load user mappings
    users_file = os.path.join(extract_dir, "users.json")
    if not os.path.exists(users_file):
        raise FileNotFoundError(f"No 'users.json' file found in {zip_file_path}.")
    user_mappings = load_users_mapping(users_file)

    # Parse channels and analyze data
    channels_file = os.path.join(extract_dir, "channels.json")
    if not os.path.exists(channels_file):
        raise FileNotFoundError(f"No 'channels.json' file found in {zip_file_path}.")
    with open(channels_file, "r", encoding="utf-8") as f:
        channels = json.load(f)

    user_posts = []
    user_threads = Counter()
    user_reactions_given = Counter()
    reactions_received = Counter()
    co_posters = Counter()
    channel_post_counts = Counter()
    replies_per_thread = defaultdict(list)

    for channel in channels:
        channel_name = channel["name"]
        channel_dir = os.path.join(extract_dir, channel_name)
        if not os.path.exists(channel_dir):
            continue

        (
            posts,
            threads,
            reactions_given,
            reactions_rcvd,
            co_posters_in_channel,
            replies_in_channel,
        ) = process_channel_messages(channel_dir, user_id, user_mappings)

        user_posts.extend(posts)
        user_threads.update(threads)
        user_reactions_given.update(reactions_given)
        reactions_received.update(reactions_rcvd)
        co_posters.update(co_posters_in_channel)
        channel_post_counts[channel_name] += len(posts)
        for thread, replies in replies_in_channel.items():
            replies_per_thread[thread].extend(replies)

    # Calculate average replies to threads started
    total_replies = sum(len(replies) for replies in replies_per_thread.values())
    threads_started = user_threads["started"]
    avg_replies = total_replies / threads_started if threads_started > 0 else 0

    # Generate the report
    top_channels = channel_post_counts.most_common(5)
    top_reaction_given = user_reactions_given.most_common(1)
    top_reaction_received = reactions_received.most_common(1)
    top_co_posters = [
        (user_mappings.get(user, user), count)
        for user, count in co_posters.most_common(3)
    ]

    report = {
        "user": user_mappings.get(user_id, user_id),
        "threads_started": threads_started,
        "replies": user_threads["replied"],
        "top_channels": top_channels,
        "most_used_reaction": top_reaction_given[0] if top_reaction_given else None,
        "most_reactions_received": top_reaction_received[0]
        if top_reaction_received
        else None,
        "top_co_posters": top_co_posters,
        "average_replies_to_threads_started": round(avg_replies, 2),
        "engagement_received": sum(reactions_received.values()) + total_replies,
    }

    return report

def find_top_contributors(zip_file_path):
    # Unpack the zip file
    extract_dir = "/tmp/slack_export"
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    # Load user mappings
    users_file = os.path.join(extract_dir, "users.json")
    if not os.path.exists(users_file):
        raise FileNotFoundError(f"No 'users.json' file found in {zip_file_path}.")
    user_mappings = load_users_mapping(users_file)

    # Parse channels and analyze data
    channels_file = os.path.join(extract_dir, "channels.json")
    if not os.path.exists(channels_file):
        raise FileNotFoundError(f"No 'channels.json' file found in {zip_file_path}.")
    with open(channels_file, "r", encoding="utf-8") as f:
        channels = json.load(f)

    # Counters for thread creators and repliers
    thread_creators = Counter()
    repliers = Counter()
    ignored_users = []

    for channel in channels:
        channel_name = channel["name"]
        channel_dir = os.path.join(extract_dir, channel_name)
        if not os.path.exists(channel_dir):
            continue

        for file_name in os.listdir(channel_dir):
            if not file_name.endswith(".json"):
                continue

            with open(os.path.join(channel_dir, file_name), "r", encoding="utf-8") as f:
                messages = json.load(f)

            threads = {}
            for message in messages:
                # Skip messages without a timestamp
                if "ts" not in message:
                    continue

                thread_ts = message.get("thread_ts", message["ts"])
                if thread_ts not in threads:
                    threads[thread_ts] = []
                threads[thread_ts].append(message)

            for thread_ts, thread_messages in threads.items():
                thread_owner = thread_messages[0].get("user", "")
                if thread_owner and thread_owner not in ignored_users:
                    thread_creators[thread_owner] += 1

                for message in thread_messages[1:]:  # Exclude the thread starter
                    user = message.get("user", "")
                    if user and user not in ignored_users:
                        repliers[user] += 1

    # Get top 5 thread creators and repliers
    top_thread_creators = [
        (user_mappings.get(user, user), count)
        for user, count in thread_creators.most_common(5)
    ]
    top_repliers = [
        (user_mappings.get(user, user), count)
        for user, count in repliers.most_common(5)
    ]

    return {
        "top_thread_creators": top_thread_creators,
        "top_repliers": top_repliers,
    }


def calculate_base_stats(zip_file_path, excluded_user_ids):
    """Calculate base stats for all users and save them."""
    extract_dir = "/tmp/slack_export"
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    # Load user mappings
    users_file = os.path.join(extract_dir, "users.json")
    if not os.path.exists(users_file):
        raise FileNotFoundError("No 'users.json' file found.")
    user_mappings = load_users_mapping(users_file)

    # Parse channels
    channels_file = os.path.join(extract_dir, "channels.json")
    if not os.path.exists(channels_file):
        raise FileNotFoundError("No 'channels.json' file found.")
    with open(channels_file, "r", encoding="utf-8") as f:
        channels = json.load(f)

    user_stats = defaultdict(lambda: {
        "threads_started": 0,
        "replies": 0,
        "engagement_received": 0,
        "reactions_received": Counter(),
        "reactions_given": Counter(),
        "co_posters": Counter(),
        "top_channels": Counter(),
    })

    for channel in channels:
        channel_name = channel["name"]
        print("Processing channel:", channel_name)
        channel_dir = os.path.join(extract_dir, channel_name)
        if not os.path.exists(channel_dir):
            continue

        for file_name in os.listdir(channel_dir):
            if not file_name.endswith(".json"):
                continue

            with open(os.path.join(channel_dir, file_name), "r", encoding="utf-8") as f:
                messages = json.load(f)

            threads = {}
            for message in messages:
                if "ts" not in message:
                    continue
                thread_ts = message.get("thread_ts", message["ts"])
                threads.setdefault(thread_ts, []).append(message)

            for thread_ts, thread_messages in threads.items():
                thread_owner = thread_messages[0].get("user", "")
                if thread_owner:
                    user_stats[thread_owner]["threads_started"] += 1
                    user_stats[thread_owner]["top_channels"][channel_name] += 1

                thread_users = set()
                for message in thread_messages:
                    user = message.get("user", "")
                    if user:
                        thread_users.add(user)
                        user_stats[user]["replies"] += 1
                        user_stats[user]["top_channels"][channel_name] += 1

                    # Track reactions received
                    for reaction in message.get("reactions", []):
                        if user:
                            user_stats[message.get("user", "")]["reactions_received"][reaction["name"]] += len(reaction["users"])

                    # Track reactions given
                    for reaction in message.get("reactions", []):
                        for reactor in reaction.get("users", []):
                            user_stats[reactor]["reactions_given"][reaction["name"]] += 1

                # Track co-posters
                for user in thread_users:
                    for other_user in thread_users:
                        if user != other_user and other_user not in excluded_user_ids:
                            user_stats[user]["co_posters"][other_user] += 1

    # Finalize stats
    for user, stats in user_stats.items():
        stats["most_reactions_received"] = stats["reactions_received"].most_common(1)
        stats["most_used_reaction"] = stats["reactions_given"].most_common(1)
        stats["top_channels"] = stats["top_channels"].most_common(5)
        stats["top_co_posters"] = stats["co_posters"].most_common(3)

        # Calculate total engagement (replies + reactions received)
        total_replies = stats["replies"]
        total_reactions = sum(stats["reactions_received"].values())
        stats["engagement_received"] = total_replies + total_reactions

        # Simplify reaction stats
        stats.pop("reactions_received", None)
        stats.pop("reactions_given", None)
        stats.pop("co_posters", None)


    # Save base stats
    with open("base_stats.json", "w") as f:
        json.dump(user_stats, f, indent=2)



def calculate_percentiles(base_stats_file, excluded_user_ids):
    """Calculate percentile stats, excluding certain users from percentile contributions."""
    with open(base_stats_file, "r") as f:
        base_stats = json.load(f)

    stats_keys = ["threads_started", "replies", "engagement_received"]

    # Prepare lists for active users only, excluding specified user IDs
    active_stats_data = {key: [] for key in stats_keys}
    for user, stats in base_stats.items():
        if user not in excluded_user_ids and (stats["threads_started"] > 0 or stats["replies"] > 0):
            for key in stats_keys:
                active_stats_data[key].append(stats.get(key, 0))

    # Calculate percentiles based on non-excluded users
    percentiles = {key: np.percentile(active_stats_data[key], np.arange(0, 101)) for key in stats_keys}

    # Assign percentile ranks for all users, including excluded ones
    for user, stats in base_stats.items():
        if stats["threads_started"] > 0 or stats["replies"] > 0:
            for key in stats_keys:
                user_value = stats.get(key, 0)
                # Percentile is calculated based on non-excluded users
                stats[f"{key}_percentile"] = 101 - int(np.searchsorted(percentiles[key], user_value, side="right"))
        else:
            # Inactive users get 0 for all percentile stats
            for key in stats_keys:
                stats[f"{key}_percentile"] = 0

    # Save final stats
    with open("final_stats.json", "w") as f:
        json.dump(base_stats, f, indent=2)

def fix_zeros():
    with open("final_stats.json", "r") as f:
        final_stats = json.load(f)
    
    for user, stats in final_stats.items():
        if stats['engagement_received_percentile'] == 0:
            if stats['engagement_received'] > 0:
                stats['engagement_received_percentile'] = 1
            else:
                stats['engagement_received_percentile'] = 100
        if stats['replies_percentile'] == 0:
            if stats['replies'] > 0:
                stats['replies_percentile'] = 1
            else:
                stats['replies_percentile'] = 100
        if stats['threads_started_percentile'] == 0:
            if stats['threads_started'] > 0:
                stats['threads_started_percentile'] = 1
            else:
                stats['threads_started_percentile'] = 100
    
    with open("final_stats.json", "w") as f:
        json.dump(final_stats, f, indent=2)


# If you want to exclude any users from calculations, add their user IDs to this list
excluded_user_ids = []

## Step 1: Calculate base stats
zip_file_path = "exports/slack_workspace.zip"
calculate_base_stats(zip_file_path, excluded_user_ids)

# Step 2: Calculate percentiles
calculate_percentiles("base_stats.json", excluded_user_ids)
fix_zeros()

# Output is saved in final_stats.json
