#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Name   : LESS Variable Extractor
# Author : Ravi S. Rāmphal
# Date   : 2015.10.26

# This is a plugin to loop through every line of a LESS file
# and extract all CSS values out into LESS variables.
# The idea is that once the variables have been prepended,
# the user can create a New View into File side-by side to rename the variables
# to be more meaningful.

# The source code here is annotated to help someone with familiarity
# with JavaScript and some Ruby, but new to Python as well as to Sublime Text plugin development,
# to get up and running.

# Note that in Python, semicolons are OPTIONAL.
# Furthermore, Python is a whitespace-significant language.
# In JavaScript, blocks are represented by braces {}.
# However, in Python, blocks are set off by colons and are "contained" using indentation.

# In Python, libraries are imported using the `import` command (contrast to Ruby's `require`).
# The `sublime` library is included to work with Sublime Text.
import sublime

# The `sublime_plugin` library is included to get access to hooks and functions necessary for plugin development.
import sublime_plugin

# The `re` library is included to give us access to regular expressions.
import re

# In Sublime Text 2, the CamelCase name of the class MUST correlate to the snake_case version of the command.
# It MUST ALSO end with the 'Command'.
# For example: `ExtractCssValuesToLessVariablesCommand` --> `extract_css_values_to_less_variables`.

# We are using a WindowCommand here since it is touching the window.
# We could done this directly within a TextCommand by using `view.window()`;
# however, this is discouraged (see: https://www.sublimetext.com/forum/viewtopic.php?f=6&t=2446).
class PromptExtractCssValuesToLessVariablesCommand(sublime_plugin.WindowCommand):
    # All Sublime Text commands must have a `run` function.
    # Classes in Python require the `self` parameter (Python does not have anything like Ruby's `@`).
    def run(self):
        # `show_input_panel` is used to show the bar at the bottom for user input.
        # For reference, here is the declaration: `show_input_panel(caption, initial_text, on_done, on_change, on_cancel)`.
        self.window.show_input_panel("Please enter a prefix:", "@var", self.on_done, None, None)

    # This is a callback for `show_input_panel`.
    # `show_input_panel` calls this and passes in the user input.
    # In this case, we have captured the input as `prefix`.
    def on_done(self, prefix):
        if self.window.active_view():
            # Since we are referencing the window to get user input, we create a WindowCommand.
            # Now that we have the input, we want to call the TextCommand passing in the input.
            # Note that while class names in Python are TitledCamelCase, Sublime Text commands are in snake_case.
            self.window.active_view().run_command("extract_css_values_to_less_variables", {"prefix": prefix})

#We are using a TextCommand to handle the simple text manipulation.
class ExtractCssValuesToLessVariablesCommand(sublime_plugin.TextCommand):
    # The `self` parameter here is required for Python's handling of classes.
    # The `edit` parameter here is passed in by Sublime Text.
    # This allows Sublime Text to capture all command changes within one undo/redo function.
    # The `prefix` parameter here is passed in by the `PromptExtractCssValuesToLessVariablesCommand` class.
    # NOTE: Unlike with JavaScript, Python, like Ruby, requires the number of parameters to match EXACTLY.
    def run(self, edit, prefix):
        # `view.sel()` returns all the selections (known as "regions" within Sublime Text) within a buffer.
        # We can consider the buffer to be the text within a tab.
        # Here we are iterating over each of them with a `for..in` control structure.
        for region in self.view.sel():
            # If the region is not empty,
            if not region.empty():
                # run the `extract_variables` function (making sure to provide Sublime's `edit` and our `region` and `prefix).
                self.extract_variables(edit, region, prefix)

    # The extract_variables will iterate over the region, generate the variables, and replace the values.
    # This could refactored to separate concerns better.
    # Note that `self` is included standard to Python object-oriented programming and we still pass through `edit`.
    def extract_variables(self, edit, region, prefix):
        # `view.line()` takes a region and expands it to include full lines.
        # This is to account for when a user begins or ends a selection in the middle of a line.
        # Regions are simply ranges of characters and are NOT the actual strings.
        full_lines = self.view.line(region)

        # `view.split_by_newlines` again takes a region and generates subregions based on new lines in the text.
        # Note that this doesn't actually return STRINGS, but however an iteratable object of REGIONS.
        lines = self.view.split_by_newlines(full_lines)

        # Here we set up a counter so that we can generate unique variable names.
        counter = 0

        # Here, we create a list to hold the final output with the list of the newly-created variables.
        # In Python, Lists serve the function that we would expect from Arrays in JavaScript and Ruby with very similar syntax.
        variables = []

        # Here, we iterate over the line regions in reverse order so as to not mess up the positions stored by `view.sel()`
        for line in reversed(lines):
            # Here, we run a regex search on each line.
            # Note that we don't get the actual string until we pass in the region into `view.substr()`.
            # We exclude the `@` character from the value so that we don't act on already-existing
            # variables.
            match = re.search(r"^(\s*)(.+)(\s*):(\s*)([^@]+)(\s*);(.*)$", self.view.substr(line))

            if match:
                # In Python, instead of using `\1` or `$1` to refer to the first regex captured group,
                # we use `match.group(1)`.
                # `match.group(0)` is the full string match itself.
                # We store these in variables here to assign meaningful names.
                # We capture the whitespace so that when we reconstruct the style declaration with the variable,
                # it will match the original whitespace.
                space_before_property = match.group(1)
                css_property          = match.group(2)
                space_after_property  = match.group(3)
                space_before_value    = match.group(4)
                css_value             = match.group(5)
                space_after_value     = match.group(6)
                inline_comments       = match.group(7)

                # Here, we increment the counter so that we can generate the variable names.
                # The Math addition operator is `+` as it is in most languages.
                counter = counter + 1

                # Here, we generate the name of the variable with a unique number and the CSS property.
                # For example: `@prefix-lessvar2-color`.
                # We add 'lessvar' to the counter so that if the user uses multiple selections to edit
                # the names of the variables, it will be distinct enough to not be confused with actual
                # numerical values within the text.
                # String concatenation is done with the `+` operator as with JavaScript and Ruby.
                # In Python, you cannot concatenate strings and integers.
                # Python will not coerce the integers as JavaScript will, and therefore we will need to
                # use the utility function `str()` to do so explicitly.
                prefixed_name = prefix + '-' + 'lessvar' + str(counter) + '-' + css_property

                # `replacement` will hold the text that will replace the CSS values.
                # For example: border-bottom: {replacement}.
                replacement   = ""

                # Here we check to see if there is a space character in the CSS value so we can handle shorthand values.
                if " " in css_value:
                    # Here, we split the value on the space so that we can generate an individual variable for each value.
                    # This will result in a list of each individual shorthand value: '1px solid black' --> ['1px', 'solid', 'black'].
                    # Generally, CSS properties with spaced values tend to be shorthands.
                    # For example: `border-width`, `border-style`, `border-color`).
                    # Therefore, within this code, we call it "shorthand".
                    shorthand = css_value.split(" ")

                    # The main complication with splitting on space is the `!important` keyword.
                    # This applies to the entirety of the value and not just the last one.
                    # Here we store the string `!important` simply to be DRY.
                    important_text = '!important'

                    # `important` is a boolean that is set to true when the last value is `!important`.
                    # Note that Python here acts like Ruby in that you can access elements from the end
                    # of a(n) list/array by using negative indices.
                    # Also note that value equivalence is tested with two equal signs `==` as in JavaScript.
                    # For a strict identity equivalence test, we would use `is` in Python.
                    # Side note: in Python, booleans are capitalized as `True` and `False` unlike JavaScript and Ruby.
                    important = shorthand[-1] == important_text;

                    # If the `important` flag is set to true, then we want to handle it separately and not in
                    # the normal flow of how we handle other shorthand values.
                    # We don't want to create a separate variable for `!important`.
                    # Instead, we want to leave `!important` as part of the style declaration and only pull out actual values.
                    # "Popping" the last element (namely the `!important`) will remove from the list so that it won't be acted upon.
                    # Note that here, we are using a one-line if statement.
                    if important: shorthand.pop()

                    # Generally, we are doing on a smaller scale to the individual shorthand variables what we
                    # are doing on a larger scale to simple values — pulling them out into their own variables.
                    # Therefore, we see similar storage variables here as we see above with
                    # `counter`, `prefixed_name` and `replacement`.
                    # `shorthand_counter` will keep track of which individual value we are looking at and we will
                    # it to generate the variable name.
                    # For example: `border: 1px solid black` will create the variables:
                    #     @prefix-lessvar3-border-lessv3sv1: 1px;
                    #     @prefix-lessvar3-border-lessv3sv2: solid;
                    #     @prefix-lessvar3-border-lessv3sv3: black;
                    shorthand_counter = 0

                    # `shorthand_replacement` will act as a small-scale version of `replacement` above to hold the text that will
                    # replace the shorthand values.
                    # For example: `@prefix-lessvar3-border-lessv3sv1 @prefix-lessvar3-border-lessv3sv2 @prefix-lessvar3-border-lessv3sv3`.
                    shorthand_replacement = ""

                    # `shorthand_variables` will hold the small-scale version of `variables` below to hold the variables that will
                    # be outputted at the end.
                    # For example:
                    #     @prefix-lessvar3-border-lessv3sv1: 1px;
                    #     @prefix-lessvar3-border-lessv3sv2: solid;
                    #     @prefix-lessvar3-border-lessv3sv3: black;
                    shorthand_variables = ""

                    # Here, we iterate over the values contained within the shorthand value.
                    for value in shorthand:
                        # We increment the counter to generate the variable name.
                        shorthand_counter = shorthand_counter + 1

                        # Here we deal with a nuance introduced by handling `!important`.
                        # If `!important` is present (if the `important` flag is set to true), but there is only one value
                        # (ex. `color: black !important;`), we don't want add the counter since it would only ever be `1`.
                        # Here, we check for this condition.
                        # Note: Unlike in JavaScript, where `length` is a property of an array (`array.length`),
                        # in Python, you must pass the list into the function `len()` to get its length.
                        if important and len(shorthand) == 1:
                            # and if it is met, we set `prop_name` to be the same as it would be for a non-shorthand declaration.
                            # Ex: `@prefix-lessvar4-color`.
                            prop_name = prefixed_name
                        # However, if this condition is not present (meaning that `!important` is present and there is more than one value)
                        else:
                            # append the `shorthand_counter` to the prefixed name.
                            # We add 'lessv{counter}sv' to the shorthand counter so that if the user uses multiple selections
                            # to edit the names of the variables, it will be distinct enough to not be confused with actual
                            # numerical values within the text.
                            # Ex: `@prefix-lessvar3-border-lessv3sv1`.
                            prop_name = prefixed_name + '-' + 'lessv' + str(counter) + 'sv' + str(shorthand_counter)

                        # We update `shorthand_variables` to include the new variable and we include a new line for the output.
                        shorthand_variables = shorthand_variables + prop_name + ': ' + value + ';\n'

                        # We also update `shorthand_replacement` to include the new variable name that will replace the shorthand values.
                        shorthand_replacement = shorthand_replacement + ' ' + prop_name

                    # Now that we have finished generating variables for each of the individual shorthand values,
                    # we can add them to the global list of output variables.
                    # Note that `list.append()` is Python's version of `array.push()` in JavaScript.
                    # Here we make use of `string.strip()` (Python's version of `string.trim()` in JavaScript).
                    # This is mainly to remove the trailing new line character `\n` that would be added above
                    # to the last individual shorthand value.
                    variables.append(shorthand_variables.strip())

                    # Here, we reconstruct the style declaration, except that we replace the original value with the shorthand variables.
                    # Note that we do honor the original whitespace by capturing it above.
                    # For example:
                    #     `    border : 1px solid black ; // comment ` -->
                    #     `    border : @prefix-lessvar3-border-lessv3sv1 @prefix-lessvar3-border-lessv3sv2 @prefix-lessvar3-border-lessv3sv3 ; // comment `
                    # We run `strip()` on `shorthand_replacement` to remove the extra space that would be added above
                    # to the first individual shorthand variable.
                    # One thing to note here: `(' ' + important_text if important else '')` is Python's version of a ternary expression.
                    # This is equivalent to: `(important ? ' ' + important_text : '')` in JavaScript:
                    #     If the `!important` keyword is present (`important` is set to True), then add it to the style declaration.
                    #     Otherwise, add nothing.
                    replacement = space_before_property + css_property + space_after_property + ':' + space_before_value + shorthand_replacement.strip() + (' ' + important_text if important else '') + space_after_value + ';' + inline_comments
                # If there are not spaces in the CSS value (meaning that it is not a shorthand and does not contain the `!important` keyword),
                else:
                    # add the variable to the global list of output variables
                    variables.append(prefixed_name + ': ' + css_value + ';')

                    # and reconstruct the style declaration replacing the CSS values with the newly-created variable.
                    replacement = space_before_property + css_property + space_after_property + ':' + space_before_value + prefixed_name + space_after_value + ';' + inline_comments

                # Now we have what we need to replace the original CSS values with the variables.
                # Here, we replace the entire line (region) with the new replacement string by using `view.replace()`.
                # `edit` is passed in to capture all command changes within one undo/redo function.
                # `line` is the REGION representing the current line.
                # `replacement` is the STRING that is to be the new line.
                self.view.replace(edit, line, replacement)

        # Now that all the values have been replaced with variables within the region,
        # we can iterate over the global list of output variables to generate the the string to prepend at the top of the selection.
        if variables:
            # Here we join all the variables with a new line character `\n` between them
            # and two new lines at the end to separate the variables from the original text.
            # Note that in JavaScript, this would be:
            #     `variables_output = (variables.reverse()).join('\n') + '\n\n';`
            variables_output = "\n".join(reversed(variables)) + '\n\n'

            # Finally, we insert this `variables_output` string of the list of variables to the top of the buffer (location 0).
            self.view.insert(edit, 0, variables_output)
