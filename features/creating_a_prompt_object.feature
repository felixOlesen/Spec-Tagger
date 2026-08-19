feat~creating_a_prompt_object~1
Feature: Creating a prompt object

  story~creating_a_successful_prompt_object~1
  Scenario: Successful Creation
    Given that there is information available to create a prompt
    And that the prompt covers a problem of an implementation change that isn't covered
    When I pass the informaiton to into the object constructor
    Then no exceptions should be thrown
