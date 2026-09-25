"""Create the offline integration fixture; production defaults are not edited.

Usage: python3 validation/make_fixture.py /tmp/jev-test
Then compile at.nim with Nim's release/ORC/threads flags in that folder.
Run TYPESAFE_API_KEY=offline-fixture ./at --save=fresh.bin --fixture-fusion
The copied jev_bridge.py is a local mock and never calls an external service.
The --fixture-fusion flag starts this fixture's trust at 0.8 to cover its branches.
"""
from pathlib import Path
import shutil
import sys

here = Path(__file__).resolve().parent
out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=True)
source = (here.parent/'at_jev.nim').read_text()

def replace(old, new):
    global source
    assert old in source, old
    source = source.replace(old, new)

replace('var AAA = 1500', 'var AAA = 16')
replace('const TARGET_GENERATIONS = 1000000', 'const TARGET_GENERATIONS = 16')
replace('for iter in startIter ..< TARGET_GENERATIONS:',
        'if "--fixture-fusion" in commandLineParams(): fusionReliability = 0.8\nfor iter in startIter ..< TARGET_GENERATIONS:')
replace('  var new_population = newSeqOfCap[Genome](pop_size)', '''  var beforeBreeding = newSeq[Hash](population.len)
  for id,g in population: beforeBreeding[id]=genomeFingerprint(g)
  var expectedParentUses=0
  var new_population = newSeqOfCap[Genome](pop_size)''')
replace('      releaseParentUse(parentUseCount, p2i) # asexual child used only p1',
        '      inc expectedParentUses\n      releaseParentUse(parentUseCount, p2i) # asexual child used only p1')
replace('      didCrossover = true', '      expectedParentUses+=2\n      didCrossover = true')
replace('  var usedParents = 0', '''  doAssert parentUseCount.foldl(a+b,0)==expectedParentUses
  for id,g in population: doAssert genomeFingerprint(g)==beforeBreeding[id]
  for g in new_population:
    doAssert g.len==AAA and validEmbedding(g[0].embedding)
    for rule in g: doAssert rule.weight==rule.weight and abs(rule.weight)<=WEIGHT_ABS_LIMIT
  for i,id in survivorIds: doAssert sameGenomeContent(new_population[i],population[id])
  if capacityFallbacks==0: doAssert parentUseCount.max<=PARENT_MAX_USES
  doAssert unresolvedDuplicates==0
  echo "PASS: generation ",iter," parent accounting, parent immutability, elite retention, valid embeddings"
  var usedParents = 0''')
(out/'at.nim').write_text(source)
for name in ('github-code.txt','jev_bridge.py'):
    shutil.copyfile(here/'fixture'/name, out/name)
print(out)
