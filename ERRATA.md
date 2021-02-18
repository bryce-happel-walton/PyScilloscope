**KNOWN BUGS:**
 - Some of the graphs will not visualize immediately. The data is still collected, and is accurate, just not displayed.
 - Rare visual bug: a graph will have a line going through it. I assume the cause of this is just the large amount of curve objects being displayed at once, but I have not confirmed.
  - If this is the case then there's likely no solution that wouldn't ruin the program for the user
   - There is a way to make the program be able to be run again after pressing 'Stop', but it does not work
   - Current workaround: close everything when 'Stop' is pressed

**NON-BUGS:**
 - Status indicator doesn't actually do anything
 - Program is a tad laggy because of PyQtGraph
 - Currently no workaround for a force close, realworld incident, etc.
  - The data will be lost
   - TODO: make log save every hour, or 30 minutes
   - User variable interval

