import { LightningElement, api } from 'lwc';

// Class name should be in CamelCase
export default class complexComponent extends LightningElement {
    // Variables should be declared with let or const
    @api greeting = 'Hello, World!';
    // Constants should be in uppercase with underscores
    CONSTANT_VALUE = 42;

    // Method names should be in camelCase
    connectedCallback() {
        // Variables should be declared with let or const
        var x = 10;
        // Magic numbers should be avoided
        var y = this.CONSTANT_VALUE + 2;

        // Inconsistent indentation
      if (x < y) {
          console.log('x is less than y');
      } else {
            console.log('x is greater than or equal to y');
        }

        // Braces should follow Stroustrup style
        if (x === 10)
            console.log('x is equal to 10');

        // Missing semicolon at the end of the line
        const z = x + y

        // Unused variable
        const unusedVariable = 'This is never used';

        // Naming conventions not followed
        const CONST_VAlue = 50;

        // Comments should be clear and concise
        // This comment is not helpful

        // Code should be properly formatted
this.someMethod();
    }

    // Methods should be organized logically
    someMethod() {
        console.log('Executing some method');
    }

    // Access specifiers should be consistent
    // This method should not be public
    publicMethod() {
        console.log('Executing public method');
    }
}
