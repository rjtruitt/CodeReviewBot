public class ExampleApexClass {

    // Class-level variable declaration without access modifiers
    String name;

    // Constructor with no access modifier
    ExampleApexClass() {
        // Variable initialization without access modifier
        name = 'John Doe';
    }

    // Method with no access modifier
    void displayMessage() {
        // Hardcoded string without using constants
        System.debug('Hello, ' + name);

        // Using System.assert without a proper error message
        System.assert(name != null, 'Name should not be null');

        // Nested if-else statements without braces
        if (name != null)
            System.debug('Name is not null');
        else
            System.debug('Name is null');

        // Variable naming not following camelCase convention
        Integer NUMBER_OF_ELEMENTS = 5;

        // Hardcoded integer value without using constants
        for (Integer i = 0; i < NUMBER_OF_ELEMENTS; i++) {
            // Variable naming not following camelCase convention
            String ELEMENT = 'Element ' + i;
            System.debug(ELEMENT);
        }

        // Using deprecated methods or classes
        Date today = Date.today();
        Integer year = today.year();
    }
}
