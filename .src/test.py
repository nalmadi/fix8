import json

with open('trial.json', 'r') as trial:
    trialData = json.load(trial)

fixations = []
for x in trialData:
    fixations.append(trialData[x][2])

sum = 0
for d in trialData:
    sum = sum + int(d)
    print(sum)

avg = sum/len(fixations)
print(avg)
