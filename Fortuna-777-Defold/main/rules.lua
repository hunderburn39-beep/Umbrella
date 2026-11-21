-- Fortuna 777: port of published V5 rules. Virtual credits only.
local M = {}
M.symbols = {
  cherry={payout=5}, lemon={payout=10}, orange={payout=15},
  grape={payout=25}, bell={payout=50}, star={payout=100}, seven={payout=250}
}
M.reels = {
  {"cherry","lemon","orange","grape","cherry","bell","lemon","seven","cherry","orange","grape","lemon","star","cherry","orange","bell","lemon","grape","cherry","star"},
  {"lemon","cherry","grape","bell","orange","cherry","star","lemon","grape","cherry","seven","orange","lemon","cherry","bell","grape","orange","star","lemon","cherry"},
  {"orange","cherry","lemon","star","grape","cherry","bell","orange","lemon","cherry","grape","seven","lemon","cherry","orange","bell","grape","star","lemon","cherry"}
}
M.lines = {{2,2,2},{1,1,1},{3,3,3},{1,3,1},{3,1,3}}
M.music_gain = 0.25
M.spin_loop = false
function M.grid(stops)
  local grid = {{},{},{}}
  for row=1,3 do
    for col=1,3 do
      local strip=M.reels[col]
      grid[row][col]=strip[(stops[col]+row-3)%#strip+1]
    end
  end
  return grid
end
function M.evaluate(grid,bet,active)
  local total,wins,kind=0,{},"none"
  local priority={none=0,cherries=1,three=2,jackpot=3}
  for i=1,active do
    local line=M.lines[i]
    local a,b,c=grid[line[1]][1],grid[line[2]][2],grid[line[3]][3]
    local win,k=0,"none"
    if a==b and b==c then
      win=bet*M.symbols[a].payout
      k=a=="seven" and "jackpot" or "three"
    elseif (a=="cherry" and 1 or 0)+(b=="cherry" and 1 or 0)+(c=="cherry" and 1 or 0)>=2 then
      win,k=bet*2,"cherries"
    end
    if win>0 then
      wins[#wins+1]={line=i,win=win,kind=k}
      total=total+win
      if priority[k]>priority[kind] then kind=k end
    end
  end
  return {total=total,lineWins=wins,kind=kind}
end
function M.spin(bet,active,random)
  assert(type(bet)=="number" and bet>=1 and bet<=10 and bet%1==0,"invalid virtual credit bet")
  assert(active==1 or active==3 or active==5,"invalid line count")
  random=random or math.random
  local stops={}
  for i=1,3 do stops[i]=random(1,#M.reels[i]) end
  local grid=M.grid(stops)
  return {stops=stops,grid=grid,cost=bet*active,result=M.evaluate(grid,bet,active)}
end
return M
