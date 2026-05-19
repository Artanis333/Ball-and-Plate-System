BEGIN { FS="," }
NR > 1 {
    tgt = $4 "," $5
    if (tgt != last) {
        printf "#%s tgt=(%s,%s) pos=(%s,%s)\n", $1, $4, $5, $2, $3
        last = tgt
    }
}
