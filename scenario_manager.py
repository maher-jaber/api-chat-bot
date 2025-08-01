from typing import Dict, Optional
import re

class ScenarioManager:
    def __init__(self):
        self.active_scenarios = {}  # session_id: scenario_state
        
    def start_scenario(self, session_id, scenario):
        self.active_scenarios[session_id] = {
            'scenario': scenario,
            'current_step': 0,
            'data': {}
        }
        
    def handle_scenario_step(self, session_id, user_input):
        if session_id not in self.active_scenarios:
            return None
            
        scenario_state = self.active_scenarios[session_id]
        scenario = scenario_state['scenario']
        current_step = scenario['steps'][scenario_state['current_step']]
        
        # Check for exit phrases
        if any(exit_phrase in user_input.lower() 
               for exit_phrase in scenario['exit_phrases']):
            del self.active_scenarios[session_id]
            return "Scénario annulé. Comment puis-je vous aider ?"
        
        # Handle both dict and list formats for answers
        answers = current_step['answers']
        if isinstance(answers, dict):  # Backward compatibility
            answers = [answers]
        
        # Find matching response
        for answer in answers:
            if re.search(answer['pattern'], user_input, re.IGNORECASE):
                response = answer['response']
                
                # Move to next step or complete
                if scenario_state['current_step'] + 1 < len(scenario['steps']):
                    scenario_state['current_step'] += 1
                    next_step = scenario['steps'][scenario_state['current_step']]
                    return f"{response}\n\n{next_step['question']}"
                else:
                    del self.active_scenarios[session_id]
                    return response
        
        return "Je n'ai pas compris. " + current_step['question']