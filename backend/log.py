import json
from datetime import datetime

def write_log(message):
    try:
        current_date = datetime.now().strftime("%Y-%d-%m")
        current_time = datetime.now().strftime("%H:%M:%S")
        log_entry = {"time": current_time, "message": message}

        try:
            with open("activity_log.json", "r+") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
                
                data.setdefault(current_date, []).append(log_entry)
                
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        except FileNotFoundError:
            with open("activity_log.json", "w") as f:
                json.dump({current_date: [log_entry]}, f, indent=4)

    except Exception as e:
        print(f"write_log failed: {e} at {datetime.now().strftime('%H:%M:%S')}")

# Usage
write_log("Your log message here")