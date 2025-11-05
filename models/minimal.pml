mtype = {
     a,
     b,
};

inline print_state(s) {
     if
     :: (s == a) -> printf("@@@ {\"state\": \"a\"}\n")
     :: (s == b) -> printf("@@@ {\"state\": \"b\"}\n")
     fi
}

mtype state;
mtype next_state;

init {
     /* initial values */
     state = a;
     print_state(state);

     do
     :: atomic {
          /* --- compute next_state --- */
          if
          :: (state == a) ->
               next_state = b

          :: (state == b) ->
               if
               :: next_state = b
               :: next_state = a
               fi

          :: else ->
               next_state = state
          fi

          /* --- commit update --- */
          state = next_state;
          print_state(state);
     }
     od;
}

#define a_p (state == a)
#define b_p (state == b)
