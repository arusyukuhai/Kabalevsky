import fftr, std/[math, sequtils, strutils]

var hre_list: seq[float64]

block:
  var f: File = open("hre.csv", FileMode.fmRead)
  defer:
    close(f)
    echo "closed"
  for line in f.lines:
    hre_list.add(line.split(",")[1].parseFloat)

proc he_of_dyad(r1: float64, r2: float64, r3: float64): float64 =
  var ratio = abs(log2((r1-r2)/(r2-r3)))*1200
  ratio = abs(ratio)
  if ratio > 7200:
    return hre_list.max
  return hre_list[int(floor(ratio))] * (ratio - floor(ratio)) + hre_list[int(
      ceil(ratio))] * (1 - (ratio - floor(ratio)))

echo he_of_dyad(pow(2.0, 7/12.0), pow(2.0, 4/12.0), 1.0)
echo he_of_dyad(pow(2.0, 12/12.0), pow(2.0, 7/12.0), 1.0)
echo he_of_dyad(pow(2.0, 7/12.0), pow(2.0, 3/12.0), 1.0)
echo he_of_dyad(1.5, 1.25, 1.0)
echo "\n"

let
  signal = (0..1023).mapIt(complex64(sin(TAU * 0.1 * float64(it))))

  # abs gets us back into real space
  # false for forward FFT, true for inverse (TODO flip it? separate names?)
  frequencies = fft(signal, false).mapIt(abs(it))
  # Scaling must be applied manually
  signalAgain = fft(fft(signal, false), true).mapIt(abs(it)/signal.len.float64)
#echo signalAgain
