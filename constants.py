# valid modes
modes = ['task','interactive']

# valid buckets
buckets = ['SIC','BC','School','Options','Lab','Personal']

# priority range
priorities = (0,10)

keys = ['task', 'date', 'priority', 'bucket', 'reminders']

# System prompts
PROMPT = """For this response I only want a JSON file nothing else ever. Your response should parse the input for one of 2 modes. the first mode is Task mode. This mode takes tasks, reminders, etc. pulled from the response and outputs the task in JSON format defined later. The interactive mode is more open ended in which you take a question or query and work as an LLM to give a response.
There may be multiple tasks in any given query and there can be a query with both a task and a open ended question, but there should never be a response in which you output multiple interactive strings.
the outputs should look like this [{"mode": "interactive", "response": "..."},{"mode": "task", "task": "...","date": date pulled, "priority": estimated priority, "bucket": correct sublist, "reminders": needed reminders}] a nested list of dictionaries for each section of the query.
the buckets should be one of the following ['SIC','BC','School','Options','Lab','Personal']. SIC is student investment club or related work, BC is brother connections or related work, school is general school stuff/HW, Options is anything related to the Options and Futures club, Lab is investment lab/silk analyst related, and finally personal is the misc catch all bucket.
If in task mode I would also like you to assign an estimated priority to each task which will be used to rank them in a planner. Your estimation should take time till deadline and importance to me into consideration. It should be a float 0-10, 0 being unimportant right now, deadline in months etc. 10 being I need to look within the hour, requires immediate attention, and 5 being hw in a few days I should know exist but wont end the world if I dont look right now. a 3 would be deadline in a week, 7 would be deadline tonight or some amount of attention required within 24 hours.
Date pulled should be of the format yyyy-mm-dd. The reminder should be another date with a time chosen based on information gathered for example if I have a meeting at 2pm a reminder 30 minutes before or something of that sorts so the full output looks like yyyy-mm-dd HH:MM. Things can change depending on prep time needed.
Also the output doesn't have a specific order needed the format of any given task or interactive term should be in the specified format though as long as only 1 interactive term and they are in the desired format."""

RETRY_PROMPT = """Your previous response was not in the correct format. Please reformat your response following these rules strictly:
1. Return only valid JSON, no preamble or explanation
2. Top level must be an array
3. Each object must have a 'mode' key that is either 'task' or 'interactive'
4. Task objects must have: task, date (yyyy-mm-dd), priority (float 0-10), bucket (one of SIC/BC/School/Options/Lab/Personal), reminders (yyyy-mm-dd HH:MM)
5. Interactive objects must have a 'response' key
6. Only one interactive object per array is allowed
Your message failed due to:"""
#Kill Phrases
kills = ['kill','exit','stop','bye','quit']