// Native reference board foundation; not a complete 68000 or console.
#include <array>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <vector>
#include <stdexcept>
#include <iterator>
#ifdef __SWITCH__
#include <switch.h>
#endif
class Board {
public:
 std::vector<uint8_t> rom;
 std::array<uint8_t,65536> ram{};
 uint32_t pc=0, ssp=0;
 uint8_t read8(uint32_t a) const {
  a &= 0xffffff;
  if(a<0x400000 && a<rom.size()) return rom[a];
  if(a>=0xe00000) return ram[a&0xffff];
  throw std::runtime_error("unmapped byte read");
 }
 uint16_t read16(uint32_t a) const {
  if(a&1) throw std::runtime_error("unaligned word");
  return (uint16_t(read8(a))<<8)|read8(a+1);
 }
 uint32_t read32(uint32_t a) const {return (uint32_t(read16(a))<<16)|read16(a+2);}
 void write8(uint32_t a,uint8_t v) {
  a &= 0xffffff;
  if(a<0xe00000) throw std::runtime_error("unmodeled write");
  ram[a&0xffff]=v;
 }
 void reset() {
  auto sp=read32(0), entry=read32(4);
  if((sp|entry)&1 || sp>0xffffff || entry>0xfffffe) throw std::runtime_error("invalid reset vectors");
  ssp=sp; pc=entry;
 }
};
int main(int argc,char**argv){
#ifdef __SWITCH__
 consoleInit(nullptr);
 const char* path="sdmc:/switch/MegaDrive-NX-Next/game.bin";
#else
 const char* path=argc>1?argv[1]:"game.bin";
#endif
 try {
  std::ifstream f(path,std::ios::binary);
  if(!f) throw std::runtime_error("ROM not found");
  Board b;
  b.rom.assign(std::istreambuf_iterator<char>(f),{});
  b.reset();
  std::printf("Reset SSP=%08x PC=%08x first opcode=%04x\n",unsigned(b.ssp),unsigned(b.pc),unsigned(b.read16(b.pc)));
  std::puts("Native bus diagnostic only; CPU execution not yet ported.");
 } catch(const std::exception& e){std::printf("Error: %s\n",e.what());}
#ifdef __SWITCH__
 PadState pad;
 padConfigureInput(1,HidNpadStyleSet_NpadStandard);
 padInitializeDefault(&pad);
 while(appletMainLoop()){padUpdate(&pad);if(padGetButtonsDown(&pad)&HidNpadButton_Plus)break;consoleUpdate(nullptr);}
 consoleExit(nullptr);
#endif
 return 0;
}
