mtype = {
     a,
     b,
};

inline print_state(s, timer) {
     if
     :: (s == a) -> printf("@@@ {\"state\": \"a\", \"timer\": %d}\n", timer)
     :: (s == b) -> printf("@@@ {\"state\": \"b\", \"timer\": %d}\n", timer)
     fi
}

#define MAX_TIMER 9

mtype state;
int timer;

mtype next_state;
int next_timer;

init {
     /* initial values */
     state = a;
     timer = 1;
     print_state(state, timer);

     do
     :: atomic {
          /* --- compute next_state --- */
          if
          :: (state == a) ->
               next_state = b

          :: (state == b && timer < MAX_TIMER) ->
               if
               :: next_state = b
               :: next_state = a
               fi

          :: (state == b && timer >= MAX_TIMER) ->
               next_state = a

          :: else ->
               next_state = state
          fi

          /* --- compute next_timer --- */
          if
          :: (next_state != state) -> next_timer = 1
          :: (next_state == state && timer < MAX_TIMER) -> next_timer = timer + 1
          :: else                  -> next_timer = timer
          fi

          /* --- commit updates --- */
          state = next_state;
          timer = next_timer;
          print_state(state, timer);
     }
     od;
}

#define a_p (state == a)
#define b_p (state == b)
