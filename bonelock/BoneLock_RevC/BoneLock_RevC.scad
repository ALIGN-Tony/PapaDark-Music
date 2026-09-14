// BoneLock Rev C — 150 ft storage target, 18 AWG / 2.05 mm jacket OD.
// Mechanical / analyzer prototype only; no load or RF power rating.
// Millimeters. part: body, keeper, assembly. STLs export print-oriented.
part="assembly";
$fn=80;
base_t=12;
post_d=12;
post_h=8;
keeper_gap=0.4;
screw_d=3.4;
roof_t=3;
module rr(x,y,w,h,r) {
 translate([x+r,y+r]) hull() for(a=[0,w-2*r],b=[0,h-2*r]) translate([a,b]) circle(r=r);
}
module shoulders_neck() {
 union() {
  rr(0,-42,44,84,10);
  rr(180,-42,14,84,6);
  rr(186,-10,49,20,8);
  translate([234,0]) circle(r=16);
 }
}
module core() {
 // Clear winding zone x=44..180: 136 mm.
 // Cross-section 48 x 12 mm, four 2 mm chamfers.
 // Transform 2D coordinates (y,z) and extrusion length into world axes.
 multmatrix([[0,0,1,30],[1,0,0,0],[0,1,0,0],[0,0,0,1]])
 linear_extrude(160)
 polygon([[-22,0],[22,0],[24,2],[24,10],[22,12],[-22,12],[-24,10],[-24,2]]);
}
module body() {
 difference() {
  union() {
   linear_extrude(base_t) shoulders_neck();
   core();
   for(y=[-10,10]) translate([22,y,base_t-0.1]) cylinder(h=post_h+0.1,d=post_d);
  }
  translate([234,0,-1]) cylinder(h=base_t+2,d=16);
  for(x=[8,36]) translate([x,0,-1]) cylinder(h=base_t+2,d=screw_d);
  translate([187,32,-1]) cylinder(h=base_t+2,d=4);
 }
}
module keeper_print() {
 difference() {
  union() {
   linear_extrude(roof_t) rr(4,-24,36,48,4);
   for(x=[8,36]) translate([x,0,roof_t-0.1]) cylinder(h=post_h+keeper_gap+0.1,d=8);
  }
  for(x=[8,36]) translate([x,0,-1]) cylinder(h=roof_t+post_h+keeper_gap+2,d=screw_d);
 }
}
if(part=="body") body();
else if(part=="keeper") translate([-4,24,0]) keeper_print();
else {
 color([0.28,0.30,0.33]) body();
 color([0.9,0.45,0.12]) translate([0,0,base_t+post_h+keeper_gap+roof_t]) rotate([180,0,0]) keeper_print();
}
