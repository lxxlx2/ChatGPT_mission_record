# PRICE V3 SEARCH SPACE

Status: DESIGN_DRAFT_BLOCKED. This document is not a V3 freeze contract. No certified hidden interval exists; no optimizer or evaluator may run.

Finite global candidate sensitivity only: R1=2/2.5/3%;R2=3.5/4/4.5/5%;R3=6/7/8%;R4=10/12/14%;R5=3.5/4/4.5%;R7multiplier=2.5/3,R7move=1.5/2%. Fixed R6=1%,R8=4pp,R9=6pp. Cartesian count1296. No per-asset or HYPE parameters. GT is independent and fixed.

Tie order R1,R2,R3,R4,R5,R7_multiplier,R7_move;prefer larger values after metric ties. Exposed08:38 case does not select R3. Search is prohibited until the complete freeze contract with certified ranges, role paths and code integrity is committed and pushed.
