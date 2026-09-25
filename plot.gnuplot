set datafile separator ","
set terminal pngcairo size 1000,600
set output 'progress.png.pending'
set title "GA progress: moving-dataset training fitness (not held-out validation)"
set xlabel "generation (completed; starts at 200)"
set ylabel "mean[-log2(1 - best Spearman)]"
set grid
set key left top
set ytics nomirror
set xrange [200:210]
set yrange [3.08183036:3.11252164]
set y2label "Jev fresh rank-weighted quality MA10 (not accuracy)"
set y2tics
set y2range [0.03331239987912158:0.03563239987912158]

# The saved CSV uses zero-based iter. Display iter 199 as generation 200.
# Never connect lines to Jev observations from before completed generation 200.
plot 'progress.csv' using (($1+1 >= 200) ? $1+1 : 1/0):4 axes x1y1 \
       with linespoints pt 7 ps 0.35 lw 2 title 'Spearman MA200', \
     "ga_checkpoint.bin.jev_progress.csv" using (($1+1 >= 200) ? $1+1 : 1/0):3 axes x1y2 with linespoints pt 5 ps 0.45 lw 2 title 'Jev fresh rank-weighted MA10 (current settings)'
