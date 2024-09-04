

resource "jamfpro_computer_extension_attribute" "computer_extension_attribute_001" {
  name        = "tf-ghatest-cexa-popup-menu-example"
  enabled     = true
  description = "An attribute collected from a pop-up menu."

  input_type  = "Pop-up Menu"
  input_popup = ["Option 1", "Option 2", "Option 3"]


  inventory_display = "User and Location"
}

# resource "jamfpro_computer_extension_attribute" "computer_extension_attribute_002" {
#   name        = "tf-example-cexa-text-field-example"
#   enabled     = true
#   description = "An attribute collected from a text field."

#   input_type        = "Text Field"
#   inventory_display = "Hardware"
# }

# resource "jamfpro_computer_extension_attribute" "computer_extension_attribute_003" {
#   name         = "tf-example-cexa-hello-world"
#   enabled      = true
#   description  = "An attribute collected via a script."
#   input_type   = "script"
#   input_script = "#!/bin/bash\necho 'Hello, World!!!!! :)'"

#   inventory_display = "General"
# }

# resource "jamfpro_computer_extension_attribute" "computer_extension_attribute_004" {
#   name         = "tf-example-cexa-system_extensions"
#   enabled      = true
#   description  = "An attribute collected via a script."
#   input_type   = "script"
#   input_script = file("support_files/computer_extension_attributes/system_extensions.sh")

#   inventory_display = "Operating System"
# }
