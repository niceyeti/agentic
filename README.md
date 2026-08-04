# READEMS

This project is a personal intro LangGraph for training. The purpose is to learn
LangGraph, but primarily it is to understand the operational project structure
of multi-agent projects as a unit-of-work and the control plane reqs needed to
secure them. It appears in 2026 that agentic control planes are still
forthcoming.

LangGraph is a pretty thin workflow language for agentic apps, though the
application layer features like vector stores are terrific. However agentic apps
do ultimately resemble nanoservices, essentially just aggregating llm apis and
implementing the app requirements of agents. However this agent will probably
stay pretty simple, since the real meat is in the control plane with which an
app like this would integrate to provide all of the ilities and CNCF best
practices: mTLS, A2A comms, secret injection, traceability, and so on.

Gist:
- basic multi-agent functionality
- demonstrated ops (key management, control plane integration)
- HITL
- security and attack tree analyses



References:
* [flow](https://www.youtube.com/watch?v=C5ealSUWPxY&list=RDC5ealSUWPxY&start_radio=1&pp=ygUUcmFtamFtIHNsb3dlZCByZXZlcmKgBwE%3D)

```
. ._vvi.... ....                                                                                        
 .:vllIi   . .                                                                                          
. =IIIIl .. ..      .                                                                                   
 . {i::~. . ..    .      .    .   .  .    .   .   .  .   .  .   .  .   .          .   .  .   .    .    .
 .  -:: . . .                                                              .  .                         
. . .:=.. . .                            .                                                       .      
 . . :;. : .   .        .   .    .               .                       .         .                  . 
 . . .;:.          .                  .       .       .  .   .  .   .                  .   .  .         
. . . =:               .        .                                       .        .                  .   
  . . =;.    .   .            .      .    .          .                         .                  .     
 ..   =;:                  .                  .   .           .    .                                    
..    ;;;                           .                     .                           .   .   .         
.     :=;.  .   .   .  .      .  .       .   .         .                                                
      :;;:                 .                      .                                 .             .   . 
.     .=;:     .                        .   .                      .                                    
     ..=;;.         .  .        .   .                            .::.: .                        .       
      .--:...      .       .               .                     .:;;.-::.. .                           
     __vIvIvv|,           .                                        ::.. --::..                          
    _nvvl>"^+==__.     .        .   .  .                             :..   .-;..                        
 . .v"~_=|||||||+||||_.        .                                       ...: ..:.                        
.  ._=||||+|+|+||+||+|||_..  .                                             ...:=.                       
 .=||||||+||+||+||+||||+||=,                                                  ..:..                     
_|||+|+|+||+||+||+||+|+|||||;                                                  .:...                    
|||+|||+||+||+||+||+|||+|+|+|| .  .                                            .:   ..                  
||+||+||+||+|||+||+||+|+||+||+|                                                .:     .                 
+|||+||+||+||+|||+||+||+|+||+|||  .                                            .:                       
||+|+|+||+||+|+|+||+||+||||+||+|;                                              .:                       
|+||||||+||+|||||+|||+||+|+||+|||.                                             .:                       
+||+|+|+||+||+|+|||+|||+||||+||+|;                                             .:                       
||+||+|||+||+|||+|+||+|||+|+||+||;                                             ::                       
|+||+||+|||+||+||+||+||+||+||+||+|                                             =:                       
+||+||+||+|||+||+||+|+||+|||+|++++                                            .=:                       
+||||+||+||+|+||+|-~~-=_____<|ivlvIvvIvvvvvvvii_                             .:=:                       
||+|+||+||+|+-=,vlvvvvvII|""""^^^^~~-~~~~~~^^^{vv|                            ==:                       
|+|||+|||+|-_vvv>""^`                          -<vi                          .;=:.                      
|||+|||+;=_nvv}`                                 +v(                         .=;;                       
+|+||+|:%vvvI%                                    <i.                        .=;;                       
|||+|+:vlIIlv`                                    -l=                       .:==;:                      
|+||=_nlIvlI>                                      lv                       .==;=.                      
+||+:vvvIIIv;                                      <v;                      :=;=;.                      
||+=)IvIIvlI;    __a,   _aaaaas.aaaauww   .waaa.   %v;                     .:==;=:                      
|+|;vlIvIIvI;aammmm#[   j#ZZZZU=#ZZ####a_aaZ#Z#'   vv;                     .;=;=;:                      
+||:IvIvlIIv;m######6ssad###m##]##m##m##m#Z##m#   :lI`                     .=;;=;:                      
||+;vIIvIIIIv]##m#mm##Z######mf###mmm#####mm##f   )l%                      .;==;=.                      
|+|;vlvIIvIII;X##m#m##########`4Xm####m#mmmm#Z   )lI'                      .==;=;.                      
+||:IIvIvlIIvv/$###mmmmm#####^  !##mm######U! ._>lI`                       .|||=; .                     
||+;vIIvlvIvIII/4Zm##m#mm#UX"    -????v|=__i|lvvv>`                       ::<>+|+_                      
|+|=<lIIIvIIIIvvi__=____==|illlivvvIvIvvvnnIIvIv~                      .--.+|;++++.                     
+|||.vIIIIIvIIIlIvnnvnnnnvvvIvIvllIIvIIIIvlvII"                    ....:..:===:|=|                      
||+|=+vIvIIvIIvIvIIIvIIlIIIIIIIIIvIvlvIvIlII"                    .-......-..-:.-==                      
|+|||_{lIIvlvIIIIIIIIIIvIvvIvIvIvIIIIIIIIv>`       _;||__    . :.-.....-...-..:=-                       
||+|+|;<vIIIvIvIIvII>""~~::_______;=+^<v>         =||||||| ,.......:....-.:.. .                         
+||+|||_++il||"^<=__=+|||||||||||||||+=          =||||+=-.ii:...-.-. ..-.-. .                           
||+||+||||+=|||||||||||+|+||+|+|+|+|+||.        :||++-.==.i>.....-..:....                               
|+|||||+|||||+|+|+|+||+|||+|||+||+|||||:        |=.`:+=:|l+........-.                                   
|||+|+||+|+|+|||+|||+||+|+||+|+|+||+|+|:        -.:ii|ii>.....-.....                                    
+|+||+|+|||+||+|||+||+||+||+||||||+||+|;        ...~`:ii;...-...__=|.                                   
|+||+|||+|+||||+|+||+||+||+||+|+|+||+||=       - :.:.-~~i -...,|||=;:                                   
+||+||+||+||+|+|||+|+|+=~-~=<s_as_=|||+=      .:.. _|:=i;~`_||:|+|=;+.                                  
+|+||+||+|+|+||+~~<a,aawmZ#]ZZ##X|||+|-       ..._|||=|||=:<||.|+`=:|=                                  
||||+||+|+||+~<au##Z[ZZZZZX]X#ZZ#+|=~           |||+|;=+||._=|.__|+:||.                                 
|+|+||+||||=aZ]ZZUZZ[XZZ#ZZ)ZZZUZ;             :||+||+;=|-=||`||||=|||=                                 
+||+|+||++=ZZU)Z#ZZ#[XZ#ZZ#>#ZUZZ;             ||+||+|||`==__=|||==|+||=                                
||+|||+|=<#Z#Z;ZZZ#Zo]X!!"?'SX#Z#;             :|||+|-=;;||||||+-=|||+|| ..                             
||||+||+;dZUZZ;#Y!"ia_awX#2(??!!"'              |+||||||:|+|+|+`=|||+||+.===:.                          
|+|+|+||<X?!Sa,u??!Yq_assao[XZZZ#(               -|+|+||_||+>-_||||+||+;;=;;;;;:.                       
|||+||+|_au!"ocsudZZX;ZXXXZ[X#ZUZ[                .~+=~:||-=_||||||+|+|.=;:;;;;;;:.                     
||+||+||=saX##X3ZZ#Z#(UZZZ#oXZZZZ[                 -~|==_=|||||||+||||`:;;;;;;;;;; =.                   
|||+||+|=ZZZZZZ]Z#ZZZ[#ZUZZZ]#Z#ZC                     -~||+||+|+||++`:;;;;;;;;;;;.;;;.                 
|+||+|||;3ZZ#Z#]Z#ZUmh3UZY!!-!!!!!                         --~|+||+~::;;;;;;;;;;;; =;;=:                
||+||+|+|=!#XZ#)7!"Y!|___=||||++++||=                           -- ;;;;;;;;;;;;;;:.=;;;;=:.             
||||+||+||=_==__=||||||||||+|+|||||+|                               --;;;;;;;;;:;-:;;;:;;;;.            
|+|+|+||+||||||||||+|+|+|+||+||+|+|||                                   -;;;;;;;-.=;;;;;;;;;:           
=|||||+|||+||+||+|+||+|||||+|=+-~~-~-                                     --;;:.:=;;:;;;;;;;;:          
=||+|+||+|+|+||+|||=~~-:____iiIvvvvvvv_,                                     .:;;;;;;;;;;;;;;:..        
:||+|+|+|+||=~-:__>ivvIvvvvnvlIIIlIIIvvvv=,                                    :=:;;;;;;;;;;;:.=.       
:||+|-~__>iIIvvvvnvvvlIIIIvIIIvIIvvIvlIIvvvvi,                                   :;;;;;;;;;;;.:;;       
 ~=_=vIvvvlIIIIvIIvIIIIvIIIIvlIIIIIIIIvIIIvlIIs,                                  -;;;;:;;;::.=;;;      
ivvvvvlvlIvIvIvIvIvIvvIvIvvIvIvvvIvIvIIIvvIIvIlvi_                                  :;;;;;;;.=;;;;:     
vIIvIvlIvДобрый-йетиIIIIvIIIIIIIIvIvIIvIIIIIlIIIvvn,                                 :;;;;; =;;;;;;:    
IIIIIIvIIvIIvIvIIvIvIvIvIvIvvIvvIvIIIvIIvIvIvIvIvIvvi,                                ---:.=;;;;;;;;    
IIvIvIvIvIvIvIIvIvIIvlvlvlvIIIIIIvlvIIvIIIIIIIIvlIIIIvi                                .=;;;;;;;;;;;.   
vIvIIvIIvIIvIIvIIIvIIIi>"^^^""==;;_____________;++"^^+vl.                               =:;;;;;;;;;;:   
lIIIIIIvIIvlI>"^~=___;=||||||||||||||||||||||||||||||||=_                               :;;;;;;;;;;;;   
IIIIII>""<|__;=|||||||||+|+|++|+|+||+|+|+|+|+|+||+|+||+|| ,                              ;;;;;;;;:;;;.  
Il+^:_;||+|||||||+||+||||+|+||||||+||||+|+|+||+|+||||+||+.|_                             =;;;;;;;;;;;.  
_=||||||+||+||||+||+||+|+||||+|+|+||++||+||||+|||+|+|||+| ||;                            =;;;;;;;;;;;.
||||+||+||+||+|+||+||+|||+|+|+||+||+||+|||+|+||+||+||+||| |||.                          .=;;;;;;:;;;;.  
```
