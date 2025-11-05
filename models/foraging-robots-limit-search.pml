mtype = {
     resting,
     leavingHome,
     randomWalk,
     moveToFood,
     scanArena,
     grabFood,
     moveToHome,
     deposit,
     homing
};

inline print_state(s, timer, searching_timer, next_state, next_timer, next_searching_timer) {
     if
     :: (s == resting)     -> printf("@@@ {\"state\": \"resting\", \"timer\": %d, \"searching_timer\": %d, \"next_state\": %d, \"next_timer\": %d, \"next_searching_timer\": %d}\n", timer, searching_timer, next_state, next_timer, next_searching_timer)
     :: (s == leavingHome) -> printf("@@@ {\"state\": \"leavingHome\", \"timer\": %d, \"searching_timer\": %d, \"next_state\": %d, \"next_timer\": %d, \"next_searching_timer\": %d}\n", timer, searching_timer, next_state, next_timer, next_searching_timer)
     :: (s == randomWalk)  -> printf("@@@ {\"state\": \"randomWalk\", \"timer\": %d, \"searching_timer\": %d, \"next_state\": %d, \"next_timer\": %d, \"next_searching_timer\": %d}\n", timer, searching_timer, next_state, next_timer, next_searching_timer)
     :: (s == moveToFood)  -> printf("@@@ {\"state\": \"moveToFood\", \"timer\": %d, \"searching_timer\": %d, \"next_state\": %d, \"next_timer\": %d, \"next_searching_timer\": %d}\n", timer, searching_timer, next_state, next_timer, next_searching_timer)
     :: (s == scanArena)   -> printf("@@@ {\"state\": \"scanArena\", \"timer\": %d, \"searching_timer\": %d, \"next_state\": %d, \"next_timer\": %d, \"next_searching_timer\": %d}\n", timer, searching_timer, next_state, next_timer, next_searching_timer)
     :: (s == grabFood)    -> printf("@@@ {\"state\": \"grabFood\", \"timer\": %d, \"searching_timer\": %d, \"next_state\": %d, \"next_timer\": %d, \"next_searching_timer\": %d}\n", timer, searching_timer, next_state, next_timer, next_searching_timer)
     :: (s == moveToHome)  -> printf("@@@ {\"state\": \"moveToHome\", \"timer\": %d, \"searching_timer\": %d, \"next_state\": %d, \"next_timer\": %d, \"next_searching_timer\": %d}\n", timer, searching_timer, next_state, next_timer, next_searching_timer)
     :: (s == deposit)     -> printf("@@@ {\"state\": \"deposit\", \"timer\": %d, \"searching_timer\": %d, \"next_state\": %d, \"next_timer\": %d, \"next_searching_timer\": %d}\n", timer, searching_timer, next_state, next_timer, next_searching_timer)
     :: (s == homing)      -> printf("@@@ {\"state\": \"homing\", \"timer\": %d, \"searching_timer\": %d, \"next_state\": %d, \"next_timer\": %d, \"next_searching_timer\": %d}\n", timer, searching_timer, next_state, next_timer, next_searching_timer)
     fi
}

#define TIME_R 5
#define TIME_D 5
#define MAX_TIMER 10
#define MAX_SEARCHING_TIMER 20

#define in_searching_state (state==leavingHome || state==randomWalk || state==moveToFood || state==scanArena)
#define in_next_searching_state (next_state==leavingHome || next_state==randomWalk || next_state==moveToFood || next_state==scanArena)

mtype state;
int timer;
int searching_timer;

mtype next_state;
int next_timer;
int next_searching_timer;

init {
     /* initial values */
     state = resting;
     timer = 1;
     searching_timer = 1;
     print_state(state, timer, searching_timer, next_state, next_timer, next_searching_timer);

     do
     :: atomic {
          /* --- compute next_state --- */
          if
          :: (state == resting && timer < TIME_R) ->
               if
               :: next_state = resting
               :: next_state = leavingHome
               fi
          :: (state == resting && timer >= TIME_R) ->
               next_state = leavingHome

          :: (state == leavingHome && timer == 1 && searching_timer < MAX_SEARCHING_TIMER) ->
               if
               :: next_state = leavingHome
               :: next_state = randomWalk
               fi
          :: (state == leavingHome && timer >= 2 && searching_timer < MAX_SEARCHING_TIMER) ->
               next_state = randomWalk

          :: (state == randomWalk && searching_timer < MAX_SEARCHING_TIMER) ->
               if
               :: next_state = randomWalk
               :: next_state = homing
               :: next_state = moveToFood
               fi

          :: (state == moveToFood && searching_timer < MAX_SEARCHING_TIMER) ->
               if
               :: next_state = moveToFood
               :: next_state = grabFood
               :: next_state = homing
               :: next_state = scanArena
               fi

          :: (state == scanArena && searching_timer < MAX_SEARCHING_TIMER) ->
               if
               :: next_state = scanArena
               :: next_state = homing
               :: next_state = moveToFood
               :: next_state = randomWalk
               fi

          :: (searching_timer >= MAX_SEARCHING_TIMER) ->
               next_state = homing

          :: (state == grabFood && timer == 1) ->
               if
               :: next_state = grabFood
               :: next_state = moveToHome
               fi
          :: (state == grabFood && timer >= 2) ->
               next_state = moveToHome

          :: (state == moveToHome && timer < TIME_D) ->
               if
               :: next_state = moveToHome
               :: next_state = deposit
               fi
          :: (state == moveToHome && timer >= TIME_D) ->
               next_state = deposit

          :: (state == deposit && timer == 2) ->
               if
               :: next_state = deposit
               :: next_state = resting
               fi
          :: (state == deposit && timer >= 3) ->
               next_state = resting

          :: (state == homing && timer < TIME_D) ->
               if
               :: next_state = homing
               :: next_state = resting
               fi
          :: (state == homing && timer >= TIME_D) ->
               next_state = resting

          :: else ->
               next_state = state
          fi

          /* --- compute next_timer --- */
          if
          :: (next_state != state) -> next_timer = 1
          :: (timer < MAX_TIMER)   -> next_timer = timer + 1
          :: else                  -> next_timer = timer
          fi

          /* --- compute next_searching_timer --- */
          if
          :: (in_next_searching_state != in_searching_state) ->
               next_searching_timer = 1
          :: (in_searching_state && searching_timer < MAX_SEARCHING_TIMER) ->
               next_searching_timer = searching_timer + 1
          :: else ->
               next_searching_timer = searching_timer
          fi

          /* --- commit synchronous updates --- */
          state = next_state;
          timer = next_timer;
          searching_timer = next_searching_timer;
          print_state(state, timer, searching_timer, next_state, next_timer, next_searching_timer);
     }
     od
}

#define resting_p (state == resting)
#define leavingHome_p (state == leavingHome)
#define randomWalk_p (state == randomWalk)
#define moveToFood_p (state == moveToFood)
#define scanArena_p (state == scanArena)
#define grabFood_p (state == grabFood)
#define moveToHome_p (state == moveToHome)
#define deposit_p (state == deposit)
#define homing_p (state == homing)
