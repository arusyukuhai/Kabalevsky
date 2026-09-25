# OFFLINE TEST FIXTURE. Never calls any service.
import argparse,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--input');p.add_argument('--output');p.add_argument('--model');p.add_argument('--workers');p.add_argument('--pairwise-top');a=p.parse_args()
r=json.load(open(a.input)); scores=[{'id':c['id'],'score':int(hashlib.sha256(c['text'].encode()).hexdigest()[:8],16)/0xffffffff} for c in r['candidates']]
scores.sort(key=lambda c:(-c['score'],c['id']))
json.dump(dict(version=1,generation=r['generation'],ranked_ids=[c['id'] for c in scores],scores=scores,mean_quality=sum(c['score'] for c in scores)/len(scores),comparisons=0,requests=1),open(a.output,'w'))
