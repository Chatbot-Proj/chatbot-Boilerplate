from typing import Dict, Any, Text, List, Union

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, UserUtteranceReverted, AllSlotsReset, Restarted
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction
from datetime import datetime, timedelta
import requests

class ActionBookAppointment(FormAction):
    def name(self) -> Text:
        return "action_book_appointment"
    
    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ["service", "date", "time"]
    
    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        return {
            "service": [
                self.from_entity(entity="service"),
                self.from_intent(intent="get_services", value="get_services")
            ],
            "date": [
                self.from_entity(entity="date"),
                self.from_intent(intent="deny", value=""),
                self.from_intent(intent="affirm", value="today"),
            ],
            "time": [
                self.from_entity(entity="time"),
                self.from_intent(intent="deny", value=""),
                self.from_intent(intent="affirm", value="3pm"),
            ],
        }
    
    def submit(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict]:
        service = tracker.get_slot("service")
        date = tracker.get_slot("date")
        time = tracker.get_slot("time")
        
        # Book appointment with external API
        response = requests.post(
            "https://example.com/book_appointment",
            json={
                "service": service,
                "date": date,
                "time": time
            }
        )
        if response.status_code == 200:
            dispatcher.utter_message(response="utter_confirmation")
        else:
            dispatcher.utter_message(text="Sorry, there was an error booking your appointment. Please try again later.")
        
        return [AllSlotsReset()]

class ActionSendReminder(Action):
    def name(self) -> Text:
        return "action_send_reminder"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        appointment_date = datetime.strptime(tracker.get_slot("date"), '%Y-%m-%d')
        appointment_time = datetime.strptime(tracker.get_slot("time"), '%H:%M')
        appointment_datetime = datetime.combine(appointment_date, appointment_time.time())
        reminder_datetime = appointment_datetime - timedelta(hours=1)
        reminder_text = f"Reminder: You have an appointment for a {tracker.get_slot('service')} at {appointment_time.strftime('%I:%M %p')} on {appointment_date.strftime('%A, %B %d')}."
        
        # Send reminder to user via SMS or other channel
        response = requests.post(
            "https://example.com/send_reminder",
            json={
                "phone_number": tracker.sender_id,
                "text": reminder_text,
                "reminder_time": reminder_datetime.isoformat()
            }
        )
        if response.status_code == 200:
            dispatcher.utter_message(text="We've sent you a reminder for your appointment. Thanks for choosing our barbershop!")
        else:
            dispatcher.utter_message(text="Sorry, there was an error sending your reminder. Please try again later.")
        
        return []