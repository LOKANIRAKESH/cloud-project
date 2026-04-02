from dotenv import load_dotenv; load_dotenv()
import os, boto3

kw = dict(
    region_name=os.getenv('AWS_REGION','us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
)
if os.getenv('AWS_SESSION_TOKEN'):
    kw['aws_session_token'] = os.getenv('AWS_SESSION_TOKEN')

ddb = boto3.resource('dynamodb', **kw)

print('=' * 55)
print(' DynamoDB Data Verification')
print('=' * 55)

# Users
u = ddb.Table('stressdetect-users').scan()['Items']
print(f'\n[1] USERS  — {len(u)} account(s)')
for x in u:
    print(f'   name    : {x.get("name")}')
    print(f'   email   : {x.get("email")}')
    print(f'   created : {x.get("created_at", "—")}')

# Sessions
raw = ddb.Table('stressdetect-sessions').scan()['Items']
ss  = sorted(raw, key=lambda x: str(x.get('timestamp','')), reverse=True)
print(f'\n[2] SESSIONS  — {len(ss)} scan(s) stored')
for s in ss[:5]:
    print(f'   {s.get("timestamp","—")}  score={s.get("score")}  level={s.get("level")}')
if len(ss) > 5:
    print(f'   ... + {len(ss)-5} more')

# Journal
raw = ddb.Table('stressdetect-journal').scan()['Items']
jj  = sorted(raw, key=lambda x: str(x.get('timestamp','')), reverse=True)
print(f'\n[3] JOURNAL  — {len(jj)} entr(ies) stored')
for j in jj[:5]:
    text_preview = str(j.get('text', ''))[:65]
    print(f'   {j.get("timestamp","—")}  sentiment={j.get("sentiment")}  stress={j.get("stress_score")}')
    print(f'   text: {text_preview}')
if len(jj) > 5:
    print(f'   ... + {len(jj)-5} more')

print()
print('=' * 55)
print(f' TOTAL RECORDS: {len(u) + len(ss) + len(jj)}')
print('=' * 55)
