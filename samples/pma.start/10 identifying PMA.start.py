from pma_python import core

# are you running PMA.start on localhost?
print("Are you running PMA.start? " + str(core.is_lite()))

# testing actual "full" PMA.core instance that's out there
pma_core_location = "https://yourserver/pma.core.2"
print("Are you running PMA.start at " + pma_core_location + "? " + str(core.is_lite(pma_core_location)))

# testing against a non-existing end-point
pma_core_location = "https://www.google.com"
print("Are you running PMA.start at " + pma_core_location + "? " + str(core.is_lite(pma_core_location)))