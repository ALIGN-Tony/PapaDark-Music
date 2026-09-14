// BoneLock Rev D — restyled to the approved visual concept ("initial rendering").
// 150 ft storage target, 18 AWG / 2.05 mm jacket OD. Mechanical / analyzer
// prototype only; no load or RF power rating.
// Millimeters. part: body, keeper, knob, assembly. STLs export print-oriented.
//
// Functional interface is carried over from Rev C unchanged:
//   body 250 x 84 x 12, clear winding zone x=44..180 (136 mm),
//   core 48 x 12, wrap posts d12 at (22,+/-10), screw bores d3.4 at (8,0)/(36,0),
//   support eye ID 16 (center x=231, outer edge x=250), tail hole d4 at (187,32),
//   keeper roof plane z=20.4..23.4. Rev C keepers still fit.
// Retention this revision: removable keeper + two M3x30 nylon screws, tightened
// by printed 20 mm thumb knobs (captured M3 nylon nut) — tool-free. The two
// screw bores + two posts are the defined mounting interface for the future
// quick-snap captive latch housing.

part="assembly";
$fn=80;

base_t=12;      // flat body thickness
edge_r=3;      // body edge rounding
post_d=12;
post_h=8;
keeper_gap=0.4;
screw_d=3.4;
roof_t=3;
knob_d=20;
knob_h=8;
nut_af=5.7;     // M3 nut pocket across flats (nominal 5.5 + fit)
nut_t=3.4;     // pocket depth (nut nominal 2.4)

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

// Plan silhouette: bone-lobed keeper paddle, winding waist, bone-lobed mid
// cleat, flowing neck, teardrop support eye. Eye bore and neck slot are cut
// here in 2D so their edges pick up the same rounding.
module plan2d() {
 difference() {
  union() {
   for(s=[-1,1]) translate([22,s*20]) circle(r=22);   // keeper-end lobes
   rr(0,-26,44,52,8);                                 // keeper-end web
   for(s=[-1,1]) translate([192,s*30]) circle(r=12);  // mid-cleat lobes
   rr(180,-34,16,68,6);                               // mid-cleat web
   hull() { translate([196,0]) circle(r=9); translate([220,0]) circle(r=14); }
   hull() { translate([220,0]) circle(r=14); translate([231,0]) circle(r=19); }
  }
  translate([231,0]) circle(d=16);                    // support eye, ID 16
  rr(203,-4,16,8,3.9);                                // neck strap slot (no wire)
 }
}

// Winding core: 48 x 12 bar, x=30..190, rounded long edges (cable saddle).
module core() {
 multmatrix([[0,0,1,30],[1,0,0,0],[0,1,0,0],[0,0,0,1]])
 linear_extrude(160) rr(-24,0,48,12,3);
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
   core();
   for(y=[-10,10]) translate([22,y,base_t-0.1]) translate([0,0,0.1]) post();
  }
  for(x=[8,36]) translate([x,0,0]) {
   translate([0,0,-1]) cylinder(h=base_t+2,d=screw_d);
   translate([0,0,-0.01]) cylinder(h=3,d=7);                  // head counterbore
   translate([0,0,base_t-0.79]) cylinder(h=0.8,d1=screw_d,d2=5); // top chamfer
  }
  translate([187,32,0]) {
   translate([0,0,-1]) cylinder(h=base_t+2,d=4);              // tail parking hole
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
