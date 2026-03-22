from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import colorama


class ReminderEngine:
    def __init__(self, mouth):
        self.mouth = mouth
        # SQLAlchemy jobstore hata — simple in-memory use karo
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        print(colorama.Fore.GREEN + "[Reminder] Engine Started.")

    def add_reminder(self, task_name, trigger_time: datetime):
        job_id = f"reminder_{task_name.replace(' ', '_')}_{int(trigger_time.timestamp())}"

        # self.mouth pass mat karo args mein — directly use karo
        self.scheduler.add_job(
            self.trigger_alert,
            'date',
            run_date=trigger_time,
            args=[task_name],  # ← Sirf task_name, koi object nahi
            id=job_id,
            replace_existing=True
        )

        formatted = trigger_time.strftime('%d %b %Y at %I:%M %p')
        print(f"[Reminder] Set: '{task_name}' → {formatted}")
        return formatted

    def trigger_alert(self, task_name):
        # self.mouth directly use hoga — serialize nahi karna
        alert = f"[Reminder]! {task_name}"
        print(colorama.Fore.YELLOW + f"\n {alert}\n")
        if self.mouth:
            self.mouth.speak(alert)

    def get_all(self):
        jobs = self.scheduler.get_jobs()
        if not jobs:
            return "No pending reminders."
        result = []
        for job in jobs:
            result.append(
                f"{job.args[0]} → {job.next_run_time.strftime('%d %b, %I:%M %p')}"
            )
        return "\n".join(result)

    def cancel(self, task_name):
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            if task_name.lower() in job.args[0].lower():
                job.remove()
                return f"[Cancelled] reminder for {job.args[0]}"
        return "No matching reminder found."

    def shutdown(self):
        self.scheduler.shutdown()