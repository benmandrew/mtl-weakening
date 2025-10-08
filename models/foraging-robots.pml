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

inline show_state(s) {
    if
    :: (s == resting)     -> printf("@@@ state=resting\n")
    :: (s == leavingHome) -> printf("@@@ state=leavingHome\n")
    :: (s == randomWalk)  -> printf("@@@ state=randomWalk\n")
    :: (s == moveToFood)  -> printf("@@@ state=moveToFood\n")
    :: (s == scanArena)   -> printf("@@@ state=scanArena\n")
    :: (s == grabFood)    -> printf("@@@ state=grabFood\n")
    :: (s == moveToHome)  -> printf("@@@ state=moveToHome\n")
    :: (s == deposit)     -> printf("@@@ state=deposit\n")
    :: (s == homing)      -> printf("@@@ state=homing\n")
    fi
}

#define TIME_R 5
#define TIME_D 5
#define MAX_TIMER 10

mtype state;
int timer;
int step;

mtype next_state;

init {
  /* initial values */
  state = resting;
  timer = 1;
  step = 1;

     do
     :: atomic {
          /* --- compute next_state --- */
          if
          :: (state == resting && timer < TIME_R) ->
               if
               :: next_state = resting
               :: next_state = leavingHome
               fi
          :: (state == resting && timer == TIME_R) ->
               next_state = leavingHome

          :: (state == leavingHome && timer == 2) ->
               if
               :: next_state = leavingHome
               :: next_state = randomWalk
               fi
          :: (state == leavingHome && timer == 3) ->
               next_state = randomWalk

          :: (state == randomWalk) ->
               if
               :: next_state = randomWalk
               :: next_state = homing
               :: next_state = moveToFood
               fi

          :: (state == moveToFood) ->
               if
               :: next_state = moveToFood
               :: next_state = grabFood
               :: next_state = homing
               :: next_state = scanArena
               fi

          :: (state == scanArena && timer >= 1 && timer < 5) ->
               if
               :: next_state = scanArena
               :: next_state = homing
               :: next_state = moveToFood
               :: next_state = randomWalk
               fi
          :: (state == scanArena && timer == 5) ->
               if
               :: next_state = homing
               :: next_state = moveToFood
               :: next_state = randomWalk
               fi

          :: (state == grabFood && timer == 2) ->
               if
               :: next_state = grabFood
               :: next_state = moveToHome
               fi
          :: (state == grabFood && timer == 3) ->
               next_state = moveToHome

          :: (state == moveToHome && timer < TIME_D) ->
               if
               :: next_state = moveToHome
               :: next_state = deposit
               fi
          :: (state == moveToHome && timer == TIME_D) ->
               next_state = deposit

          :: (state == deposit && timer == 3) ->
               if
               :: next_state = deposit
               :: next_state = resting
               fi
          :: (state == deposit && timer == 4) ->
               next_state = resting

          :: (state == homing && timer < TIME_D) ->
               if
               :: next_state = homing
               :: next_state = resting
               fi
          :: (state == homing && timer == TIME_D) ->
               next_state = resting

          :: else ->
               next_state = state
          fi

          /* --- compute next_timer --- */
          if
          :: (next_state != state) -> timer = 1
          :: (timer < MAX_TIMER)   -> timer = timer + 1
          fi

          /* --- commit synchronous updates --- */
          state = next_state;

          show_state(state);
          printf("@@@ {\"step\": %d, \"state\": \"%d\", \"timer\": %d}\n", _nr_pr, state, timer);
          step = step + 1;
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

ltl formula
{
     []( (leavingHome_p) -> <> (resting_p) )
}
