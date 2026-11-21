local r=require("main.rules")
local function assert_eq(a,b) assert(a==b,tostring(a).." != "..tostring(b)) end
local function grid(a,b,c)
 return {{"lemon","orange","grape"},{a,b,c},{"star","bell","seven"}}
end
assert_eq(r.evaluate(grid("seven","seven","seven"),1,1).total,250)
assert_eq(r.evaluate(grid("cherry","orange","cherry"),2,1).total,4)
assert_eq(r.evaluate(grid("lemon","orange","grape"),1,1).total,0)
assert_eq(r.evaluate(grid("cherry","cherry","cherry"),3,1).total,15)
local n=0
for a=1,20 do for b=1,20 do for c=1,20 do
 local g=r.grid({a,b,c})
 assert_eq(g[2][1],r.reels[1][a])
 assert_eq(g[2][2],r.reels[2][b])
 assert_eq(g[2][3],r.reels[3][c])
 for _,active in ipairs({1,3,5}) do
  local one=r.evaluate(g,1,active)
  local ten=r.evaluate(g,10,active)
  assert_eq(ten.total,one.total*10)
  local sum=0
  for _,w in ipairs(one.lineWins) do
   assert(w.line>=1 and w.line<=active and w.win>0)
   sum=sum+w.win
  end
  assert_eq(sum,one.total)
 end
 n=n+1
end end end
local s=r.spin(2,3,function() return 1 end)
assert_eq(s.cost,6)
assert_eq(s.stops[1],1)
print("PASS: "..n.." reel combinations and virtual-credit accounting")
