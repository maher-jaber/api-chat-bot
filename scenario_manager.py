from typing import Dict, Optional

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
            return "Scenario annulé. Comment puis-je vous aider ?"
        
        # Find matching response
        for answer in current_step['answers']:
            if re.search(answer['pattern'], user_input, re.IGNORECASE):
                response = answer['response']
                
                # Store data if needed
                if 'store' in answer:
                    scenario_state['data'][answer['store']] = user_input
                
                # Move to next step or complete
                if scenario_state['current_step'] + 1 < len(scenario['steps']):
                    scenario_state['current_step'] += 1
                    next_step = scenario['steps'][scenario_state['current_step']]
                    return f"{response}\n\n{next_step['question']}"
                else:
                    # Scenario complete - compile final response
                    del self.active_scenarios[session_id]
                    return self._compile_final_response(response, scenario_state['data'])
        
        return "Je n'ai pas compris. " + current_step['question']