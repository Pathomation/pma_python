from pma_python import core

# actual tests for PMA.start (aka PMA.core.lite)
print("Are you running PMA.start? " + str(core.is_lite()))

# testing actual "full" PMA.core instance that may or may not be out there
print("Are you running PMA.start at http://somewhere/? " + str(core.is_lite("http://somewhere")))
