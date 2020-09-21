set(JUCE_EXTRAS_PATH ${JUCE_PATH}/extras)
message("-- Enabling JUCE extra application builds")
### BINARY BUILDER
set(JUCE_BINARY_BUILDER_DIR "${JUCE_EXTRAS_PATH}/BinaryBuilder")
add_executable(juce_binary_builder "${JUCE_BINARY_BUILDER_DIR}/Source/Main.cpp")
target_link_libraries(juce_binary_builder juce ${JUCE_LIBS})