// BoneLock Rev E — one continuous smooth body per design review.
// 150 ft storage target, 18 AWG / 2.05 mm jacket OD. Mechanical / analyzer
// prototype only; no load or RF power rating.
// Millimeters. part: body, keeper, knob, assembly. STLs export print-oriented.
//
// Rev E replaces Rev D's separate lobes with a single flowing silhouette:
// shoulders blend into the winding waist through concave fillets, the mid
// bump and neck stay full width, and the wire winds directly on the rounded
// 12 mm slab. This removes the thin slotted neck (Rev D weak point).
//
// Frozen keeper interface (unchanged since Rev C — see Retention_Roadmap.md):
//   screw bores d3.4 at (8,0)/(36,0) with d7x3 counterbores underneath,
//   wrap posts d12 at (22,+/-10), body top z=12, keeper roof z=20.4..23.4.
// Retention this revision: removable keeper + two M3x30 nylon screws,
// tightened by printed 20 mm thumb knobs (captured M3 nut) — tool-free.
// The rendering's captive quick-snap latch is intentionally NOT here yet.

part="assembly";
$fn=80;

base_t=12;      // body slab thickness
edge_r=3;       // slab edge rounding
blend_r=8;      // concave blend fillet (morphological closing)
post_d=12;
post_h=8;
keeper_gap=0.4;
screw_d=3.4;
roof_t=3;
knob_d=20;
knob_h=8;
nut_af=5.7;     // M3 nut pocket across flats (nominal 5.5 + fit)
nut_t=3.4;      // pocket depth (nut nominal 2.4)

module rr(x,y,w,h,r) {
 translate([x+r,y+r]) hull() for(a=[0,w-2*r],b=[0,h-2*r]) translate([a,b]) circle(r=r);
}

// Extrude 2D children into a plate with radius-r rounded top/bottom edges,
// approximated by offset slices. Holes in the 2D shape get rounded edges too.
module rplate(h,r,steps=12) {
 union() {
  translate([0,0,r]) linear_extrude(h-2*r) children();
  for(i=[0:steps-1]) {
   a0=90*i/steps; a1=90*(i+1)/steps;
   z0=r-r*cos(a0); z1=r-r*cos(a1);
   inset=r-r*sin(a0);
   translate([0,0,z0]) linear_extrude(z1-z0+0.02) offset(delta=-inset) children();
   translate([0,0,h-z1]) linear_extrude(z1-z0+0.02) offset(delta=-inset) children();
  }
 }
}

// One continuous silhouette. offset(+blend)/offset(-blend) is a morphological
// closing: every junction gets a concave fillet, so the outline flows like the
// concept rendering with no bulbous lobes. Eye bore and strap slot are cut
// afterward so their edges pick up the plate rounding.
module plan2d() {
 difference() {
  offset(r=-blend_r) offset(r=blend_r) union() {
   rr(0,-42,46,84,14);                                // keeper shoulder
   rr(26,-24,164,48,6);                               // winding waist, x=46..190 clear
   rr(190,-40,16,80,10);                              // mid bump / right shoulder
   hull() { translate([212,0]) circle(r=20); translate([231,0]) circle(r=19); }
  }
  translate([231,0]) circle(d=16);                    // support eye, ID 16
  rr(204,-4,12,8,3.9);                                // strap slot (never a wire path)
 }
}

module post() {
 cylinder(h=2,d1=15,d2=post_d);                       // root flare
 rotate_extrude() hull() {
  square([post_d/2-2,post_h]);
  square([post_d/2,post_h-2]);
  translate([post_d/2-2,post_h-2]) circle(r=2);
 }
}

module body() {
 difference() {
  union() {
   rplate(base_t,edge_r) plan2d();
   for(y=[-10,10]) translate([22,y,base_t]) post();
  }
  for(x=[8,36]) translate([x,0,0]) {
   translate([0,0,-1]) cylinder(h=base_t+2,d=screw_d);
   translate([0,0,-0.01]) cylinder(h=3,d=7);                     // head counterbore
   translate([0,0,base_t-0.79]) cylinder(h=0.8,d1=screw_d,d2=5); // top chamfer
  }
  translate([198,32,0]) {
   translate([0,0,-1]) cylinder(h=base_t+2,d=4);                 // tail parking hole
   translate([0,0,-0.01]) cylinder(h=0.8,d1=5.6,d2=4);
   translate([0,0,base_t-0.79]) cylinder(h=0.8,d1=4,d2=5.6);
  }
 }
}

module keeper_plan2d() {
 difference() {
  rr(4,-24,36,48,10);
  for(x=[8,36]) translate([x,0]) circle(d=screw_d);
 }
}

// Printed roof-down: outer face at z=0, standoffs up.
module keeper_print() {
 difference() {
  union() {
   rplate(roof_t,1.2,5) keeper_plan2d();
   for(x=[8,36]) translate([x,0,roof_t-0.1]) rotate_extrude() hull() {
    square([2.5,post_h+keeper_gap+0.1]);
    square([4,post_h+keeper_gap-1.4]);
    translate([2.5,post_h+keeper_gap-1.4]) circle(r=1.5);
   }
  }
  for(x=[8,36]) translate([x,0,-1]) cylinder(h=roof_t+post_h+keeper_gap+2,d=screw_d);
  for(x=[16,22,28]) translate([x,0,-0.4]) rotate([90,0,0])
   cylinder(h=60,r=1,center=true);                    // grip grooves, outer face
 }
}

// Printed thumb nut: 20 mm scalloped knob, captured M3 nylon nut, tool-free.
module knob() {
 difference() {
  rotate_extrude() hull() {
   square([knob_d/2-2,knob_h]);
   translate([knob_d/2-1,1]) circle(r=1);
   translate([knob_d/2-2,knob_h-2]) circle(r=2);
   square([knob_d/2-1,1]);
  }
  for(a=[0:45:315]) rotate([0,0,a]) translate([knob_d/2+2,0,-1])
   cylinder(h=knob_h+2,r=2.8);                        // grip scallops
  translate([0,0,knob_h-nut_t]) cylinder(h=nut_t+1,d=nut_af/cos(30),$fn=6);
  translate([0,0,-1]) cylinder(h=knob_h+2,d=screw_d);
 }
}

if(part=="body") body();
else if(part=="keeper") keeper_print();
else if(part=="knob") knob();
else {
 color([0.28,0.30,0.33]) body();
 color([0.28,0.30,0.33]) translate([0,0,base_t+post_h+keeper_gap+roof_t])
  rotate([180,0,0]) keeper_print();
 color([0.9,0.45,0.12]) for(x=[8,36]) translate([x,0,base_t+post_h+keeper_gap+roof_t]) knob();
}
