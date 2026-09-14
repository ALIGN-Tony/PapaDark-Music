// BoneLock Rev F — sculpted to match the approved concept rendering.
// 150 ft storage target, 18 AWG / 2.05 mm jacket OD. Mechanical / analyzer
// prototype only; no load or RF power rating.
// Millimeters. part: body, keeper, knob, assembly. STLs export print-oriented.
//
// Rev F adds the rendering's sculpted mass on top of Rev E's continuous
// silhouette while keeping a flat printable underside:
//   - domed coil flanges on BOTH sides of the winding waist (left ridge at
//     x~42..48, mid shoulder hump at x~188..204), rising to z=16;
//   - a thick rounded support-eye ring (z=16) instead of a flat washer;
//   - subtle bone-end lobes at the keeper end;
//   - larger eye: ring OD 44, bore ID 18.
// The wire winds directly on the rounded 12 mm slab between the flanges.
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
lump_h=4;       // sculpted flange height above slab (top z = 16)
post_d=12;
post_h=8;
keeper_gap=0.4;
screw_d=3.4;
roof_t=3;
knob_d=20;
knob_h=8;
nut_af=5.7;     // M3 nut pocket across flats (nominal 5.5 + fit)
nut_t=3.4;      // pocket depth (nut nominal 2.4)
eye_c=228;      // support-eye center x
eye_or=22;      // ring outer radius (outer edge at x=250)
eye_ir=9;       // bore radius (ID 18)

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

// Quarter-round domed cap of radius r over the 2D child (z = 0..r).
module dometop(r,steps=8) {
 for(i=[0:steps-1]) {
  a0=90*i/steps; a1=90*(i+1)/steps;
  translate([0,0,r*sin(a0)]) linear_extrude(r*sin(a1)-r*sin(a0)+0.02)
   offset(delta=-r*(1-cos(a1))) children();
 }
}

// A sculpted lump: embeds 2 mm into the slab top, rises to z = 12 + lump_h
// with a fully domed crown. children() = its 2D plan.
module lump() {
 translate([0,0,base_t-2]) {
  linear_extrude(2+0.01) children();
  translate([0,0,2]) dometop(lump_h) children();
 }
}

// Sculpt plans: skinny ellipses become the render's coil flanges.
module left_flange2d()  { rr(42,-40,6,80,3); }
module mid_shoulder2d() { rr(188,-40,16,80,8); }

// One continuous silhouette. offset(+blend)/offset(-blend) is a morphological
// closing: every junction gets a concave fillet, so the outline flows like the
// concept rendering with no bulbous lobes. Eye bore and strap slot are cut
// afterward so their edges pick up the plate rounding.
module plan2d() {
 difference() {
  offset(r=-blend_r) offset(r=blend_r) union() {
   rr(0,-36,46,72,12);                                // keeper deck
   for(s=[-1,1]) translate([16,s*30]) circle(r=12);   // bone-end lobes
   rr(26,-24,162,48,6);                               // winding waist, to x=188
   left_flange2d();                                   // left coil flange base
   mid_shoulder2d();                                  // mid shoulder base
   hull() { translate([206,0]) circle(r=14); translate([eye_c,0]) circle(r=eye_or); }
  }
  translate([eye_c,0]) circle(r=eye_ir);              // support eye, ID 18
  hull() for(x=[209.5,210.5]) translate([x,0]) rotate(2.25)
   circle(r=3.5);                                     // strap slot x=206..214 (never a wire path)
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

// Thick rounded support-eye ring, flat-bottomed, domed rim (z = 0..16).
module eye_ring() {
 translate([eye_c,0,0]) rotate_extrude() hull() {
  translate([eye_ir+1.5,1.5]) circle(r=1.5);
  translate([eye_or-1.5,1.5]) circle(r=1.5);
  translate([eye_or-5,11]) circle(r=5);
  translate([eye_ir+4,12]) circle(r=4);
 }
}

// Recessed maker's mark, centered on the winding waist. The panel sinks
// 1 mm into the slab top; the lettering stands 0.8 mm up inside it, so the
// text top stays 0.2 mm BELOW the winding surface and cannot chafe wire.
mark_c=118;      // panel center x (mid-waist)
module mark_panel2d() { rr(mark_c-54,-15,108,30,6); }
module mark_text() {
 translate([0,0,base_t-1]) linear_extrude(0.8) {
  translate([mark_c,8.5]) text("DESIGNED BY",size=5.5,font="Liberation Sans:style=Bold",
   halign="center",valign="center",spacing=1.15);
  translate([mark_c,-4.5]) text("K4DIA",size=14,font="Liberation Sans:style=Bold",
   halign="center",valign="center",spacing=1.05);
 }
}

module body() {
 difference() {
  union() {
   difference() {
    rplate(base_t,edge_r) plan2d();
    translate([0,0,base_t-1]) linear_extrude(2) mark_panel2d();  // mark recess
   }
   mark_text();
   lump() left_flange2d();
   lump() mid_shoulder2d();
   eye_ring();
   for(y=[-10,10]) translate([22,y,base_t]) post();
  }
  for(x=[8,36]) translate([x,0,0]) {
   translate([0,0,-1]) cylinder(h=base_t+2,d=screw_d);
   translate([0,0,-0.01]) cylinder(h=3,d=7);                     // head counterbore
   translate([0,0,base_t-0.79]) cylinder(h=0.8,d1=screw_d,d2=5); // top chamfer
  }
  translate([218,12,0]) {
   translate([0,0,-1]) cylinder(h=base_t+2,d=4);                 // tail parking hole
   translate([0,0,-0.01]) cylinder(h=0.8,d1=5.6,d2=4);
   translate([0,0,base_t-0.79]) cylinder(h=0.8,d1=4,d2=5.6);
  }
  translate([eye_c,0,-1]) cylinder(h=20,r=eye_ir);               // clear eye bore
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
  for(x=[13,19,25,31]) translate([x,0,-0.4]) rotate([90,0,0])
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
