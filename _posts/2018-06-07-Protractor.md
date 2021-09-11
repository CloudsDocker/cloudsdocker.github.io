---
title: Portactor
layout: posts
---

 
## Better to use smart wait

If possible, you'd better to use `smart wait` in protractor e2e testing. Which could increase end to end testing efficiency. Normally dev tend to use sleep or wait to insert some stop during execution. What's the difference of these two?
The difference between browser.sleep() and browser.wait() is that browser.wait() expects a specific value/condition. This wait condition is valid of Protractor or any WebDriver framework.


An Expectation for checking an element is visible and enabled such that you can click it.

```javascript
browser.wait(EC.elementToBeClickable($(‘#abc’)),5000);
```

Here are some protractor functions utilities.

### textToBePresentInElement

An expectation for checking if the given text is present in the element.
```javascript
browser.wait(EC.textToBePresentInElement($(‘#abc’),’foo’),5000);
```

### presenceOf

An expectation for checking that an element is present on the DOM of a page.
```javascript
browser.wait(EC.presenceOf($(‘#abc’)),5000);
```

```javascript
import { go, click, see, below, slow, type } from 'blue-harvest';
import { browser, ExpectedConditions } from 'protractor';

const client = 'TEST CLIENT';
const clientFullName = 'TEST CLIENT LTD';
const timeOut = 3000;

describe('Should show bell potter', () => {
    beforeEach(async () => {
        await go('http://localhost:4200/#/dashboard')
    });

    it('should be able to search bell potter', async () => {

        await slow.click('Search clients or accounts')
        await type(`TEST`);

        browser.wait(see(client), timeOut)
        await click(client)

        browser.wait(see(clientFullName), timeOut)
        expect(await below(clientFullName).see('GO')).toBeTruthy();
    })
})

```

# Reference 
* https://medium.com/@ited.ro/how-to-use-smart-waits-with-protractor-how-to-use-expected-conditions-with-protractor-10c545c670be
