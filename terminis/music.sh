#!/bin/sh

C0=-f16;   Db0=-f17;   D0=-f18;   Eb0=-f19;   E0=-f20;   F0=-f21;   Gb0=-f23;   G0=-f24;   Ab0=-f25;   A0=-f27;   Bb0=-f29;   B0=-f30
C1=-f32;   Db1=-f34;   D1=-f36;   Eb1=-f38;   E1=-f41;   F1=-f43;   Gb1=-f46;   G1=-f49;   Ab1=-f51;   A1=-f55;   Bb1=-f58;   B1=-f61
C2=-f65;   Db2=-f69;   D2=-f73;   Eb2=-f77;   E2=-f82;   F2=-f87;   Gb2=-f92;   G2=-f98;   Ab2=-f103;  A2=-f110;  Bb2=-f116;  B2=-f123
C3=-f130;  Db3=-f138;  D3=-f146;  Eb3=-f155;  E3=-f164;  F3=-f174;  Gb3=-f185;  G3=-f196;  Ab3=-f207;  A3=-f220;  Bb3=-f233;  B3=-f246
C4=-f261;  Db4=-f277;  D4=-f293;  Eb4=-f311;  E4=-f329;  F4=-f349;  Gb4=-f369;  G4=-f392;  Ab4=-f415;  A4=-f440;  Bb4=-f466;  B4=-f493
C5=-f523;  Db5=-f554;  D5=-f587;  Eb5=-f622;  E5=-f659;  F5=-f698;  Gb5=-f739;  G5=-f783;  Ab5=-f830;  A5=-f880;  Bb5=-f932;  B5=-f987
C6=-f1046; Db6=-f1108; D6=-f1174; Eb6=-f1244; E6=-f1318; F6=-f1396; Gb6=-f1479; G6=-f1567; Ab6=-f1661; A6=-f1760; Bb6=-f1864; B6=-f1975
C7=-f2093; Db7=-f2217; D7=-f2349; Eb7=-f2489; E7=-f2637; F7=-f2793; Gb7=-f2959; G7=-f3135; Ab7=-f3322; A7=-f3520; Bb7=-f3729; B7=-f3951
C8=-f4186; Db8=-f4434; D8=-f4698; Eb8=-f4978; E8=-f5274; F8=-f5587; Gb8=-f5919; G8=-f6271; Ab8=-f6644; A8=-f7040; Bb8=-f7458; B8=-f7902

dc=-l100; dcp=-l150; c=-l200; cp=-l300; n=-l400; np=-l600; b=-l800; bp=-l1200; r=-l1600

if command -v beep > /dev/null; then
  while true; do
    beep $n $E5 -n $c $B4 -n $c $C5 -n $c $D5 -n $dc $E5 -n $dc $D5 -n $c $C5 -n $c $B4 \
      -n $n $A4 -n $c $A4 -n $c $C5 -n $n $E5 -n $c $D5 -n $c $C5 \
      -n $c $B4 -n $c $E4 -n $c $Ab4 -n $c $C5 -n $n $D5 -n $n $E5 \
      -n $n $C5 -n $n $A4 -n $n $A4 -n $c $B3 -n $c $C4 \
      -n $np $D5 -n $c $F5 -n $c $A5 -n $dc $A5 -n $dc $A5 -n $c $G5 -n $c $F5 \
      -n $n $E5 -n $c $E5 -n $c $C5 -n $c $E5 -n $dc $F5 -n $dc $E5 -n $c $D5 -n $c $C5 \
      -n $c $B4 -n $c $E4 -n $c $Ab4 -n $c $C5 -n $n $D5 -n $n $E5 \
      -n $n $C5 -n $n $A4 -n $b $A4 \
      -n $n $E5 -n $c $B4 -n $c $C5 -n $c $D5 -n $dc $E5 -n $dc $D5 -n $c $C5 -n $c $B4 \
      -n $n $A4 -n $c $A4 -n $c $C5 -n $n $E5 -n $c $D5 -n $c $C5 \
      -n $c $B4 -n $c $E4 -n $c $Ab4 -n $c $C5 -n $n $D5 -n $n $E5 \
      -n $n $C5 -n $n $A4 -n $n $A4 -n $c $B3 -n $c $C4 \
      -n $np $D5 -n $c $F5 -n $c $A5 -n $dc $A5 -n $dc $A5 -n $c $G5 -n $c $F5 \
      -n $n $E5 -n $c $E5 -n $c $C5 -n $c $E5 -n $dc $F5 -n $dc $E5 -n $c $D5 -n $c $C5 \
      -n $c $B4 -n $c $E4 -n $c $Ab4 -n $c $C5 -n $n $D5 -n $n $E5 \
      -n $n $C5 -n $n $A4 -n $b $A4 \
      -n $b $E5 -n $b $C5 -n $b $D5 -n $b $B4 -n $b $C5 -n $b $A4 -n $b $Ab4 -n $c $B4 -n $c $E4 -n $c $Ab4 -n $c $B4 \
      -n $b $E5 -n $b $C5 -n $b $D5 -n $b $B4 -n $n $C5 -n $n $E5 -n $n $A5 -n $n $A5 -n $r $Ab5
  done
fi