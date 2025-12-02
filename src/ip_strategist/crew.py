import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, task, crew
from crewai.memory import Memory
from ip_strategist.llm_config import llm_call  # Your Gemini LLM wrapper

# Disable CrewAI memory to keep Gemini-only setup clean
Memory.disable()

@CrewBase
class IPStrategistCrew:
    """
    Intellectual Property Strategist Crew.

    Loads agents and tasks from YAML config files,
    builds agents with shared Gemini LLM,
    and creates a Crew to run sequential tasks.
    """

    def __init__(self):
        # Load YAML configs as dictionaries
        with open('config/agents.yaml', 'r') as f_agents:
            self.agents_config = yaml.safe_load(f_agents)

        with open('config/tasks.yaml', 'r') as f_tasks:
            self.tasks_config = yaml.safe_load(f_tasks)

    def _build_agent(self, role_key: str) -> Agent:
        """
        Helper method to create an Agent from config by role key.
        """
        cfg = self.agents_config[role_key]
        return Agent(
            role=cfg['role'],
            goal=cfg['goal'],
            backstory=cfg.get('backstory', ''),
            verbose=True,
            allow_delegation=False,
            llm=llm_call,  # Gemini LLM instance
        )

    @agent
    def patent_analyzer(self) -> Agent:
        return self._build_agent('patent_analyzer')

    @agent
    def trademark_detector(self) -> Agent:
        return self._build_agent('trademark_detector')

    @agent
    def valuation_estimator(self) -> Agent:
        return self._build_agent('valuation_estimator')

    # @agent
    # def strategy_optimizer(self) -> Agent:
    #     return self._build_agent('strategy_optimizer')

    # @agent
    # def competitor_monitor(self) -> Agent:
    #     return self._build_agent('competitor_monitor')

    @task
    def patent_analysis_task(self) -> Task:
        return Task(
            description=self.tasks_config['patent_analysis_task']['description'],
            agent=self.patent_analyzer()
        )

    @task
    def trademark_detection_task(self) -> Task:
        return Task(
            description=self.tasks_config['trademark_detection_task']['description'],
            agent=self.trademark_detector()
        )

    @task
    def valuation_estimation_task(self) -> Task:
        return Task(
            description=self.tasks_config['valuation_estimation_task']['description'],
            agent=self.valuation_estimator()
        )

    @task
    def strategy_optimization_task(self) -> Task:
        return Task(
            description=self.tasks_config['strategy_optimization_task']['description'],
            agent=self.strategy_optimizer()
        )

    @task
    def competitor_monitoring_task(self) -> Task:
        return Task(
            description=self.tasks_config['competitor_monitoring_task']['description'],
            agent=self.competitor_monitor()
        )

    @crew
    def crew(self) -> Crew:
        """
        Creates and returns the Crew instance with agents and tasks.
        Runs sequentially for rate limit safety.
        """
        return Crew(
            agents=[
                self.patent_analyzer(),
                self.trademark_detector(),
                self.valuation_estimator(),
                self.strategy_optimizer(),
                self.competitor_monitor()
            ],
            tasks=[
                self.patent_analysis_task(),
                self.trademark_detection_task(),
                self.valuation_estimation_task(),
                self.strategy_optimization_task(),
                self.competitor_monitoring_task()
            ],
            process=Process.sequential,
            verbose=True
        )
