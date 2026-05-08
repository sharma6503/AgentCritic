from adk.runner import Runner
from armor_shield.protector import ArmorShield
# ...
runner = Runner(app=app, agent=root_agent, plugins=[ArmorShield()])