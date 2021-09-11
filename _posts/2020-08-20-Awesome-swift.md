---
title: Awesome Swift for iOS
date: 2020-08-20
tags:
 - Swift
 - iOS
 - Mac
layout: posts
---

## Frame in Swift

Forgetting to assign a view a frame when creating it in code, and then wondering why it isn’t appearing when added to a superview, is a common beginner mistake. If a view has a standard size that you want it to adopt, especially in relation to its contents (like a UIButton in relation to its title), an alternative is to call its sizeToFit method.

Matt Neuburg. Programming iOS 13 (Kindle Locations 555-557). O'Reilly Media. Kindle Edition. 


# Configu a view 
Initializers, modifiers and inheritance
Overall, there are three different ways to configure a SwiftUI view — by passing arguments to its initializer, using modifiers, and through its surrounding environment.


# SF Symbols
SF Symbols provides a set of over 2,400 consistent, highly configurable symbols you can use in your app. Apple designed SF Symbols to integrate seamlessly with the San Francisco system font, so the symbols automatically ensure optical vertical alignment with text in all weights and sizes.

You can use SF symbols to represent tasks and types of content in a variety of UI elements, such as navigation bars, toolbars, tab bars, context menus, and widgets. T



## To show Avatar
```swift
// avatar
AvatarView(image: post.user.avatar, size: 70)
```

# Tricks

## Create a red calendar
Since SwiftUI views are responsible for determining their own size, we need to tell our image to resize itself to occupy all available space, rather than sticking to its default size. To make that happen, we simply have to apply the .resizable() modifier to it

```swift
        Image(systemName: "calendar")
        .resizable()
            .frame(width: 50, height: 50)
            .background(Color.red)
            .padding()
```
Again, the result of the above might not be what we were expecting, as we’ve essentially given our calendar icon outer padding — additional whitespace that doesn’t include its background color. If we think about it, this is the exact same behavior as we encountered before when applying our .frame() modifier — calling .padding() doesn’t actually mutate our earlier views and modifiers, it simply adds whitespace around the result of the preceding expressions.

## A rounded calendar view

```swift
struct CalendarView: View {
    var body: some View {
        Image(systemName: "calendar")
            .resizable()
            .frame(width: 50, height: 50)
            .padding()
            .background(Color.red)
            .cornerRadius(10)
            .foregroundColor(.white)
    }
}
```

## Add a badge

```swift
extension View {
    func addVerifiedBadge(_ isVerified: Bool) -> some View {
        ZStack(alignment: .topTrailing) {
            self

            if isVerified {
                Image(systemName: "checkmark.circle.fill")
                    .offset(x: 3, y: -3)
            }
        }
    }
}


struct CalendarView: View {
    var eventIsVerified = true

    var body: some View {
        Image(systemName: "calendar")
            .resizable()
            .frame(width: 50, height: 50)
            .padding()
            .background(Color.red)
            .cornerRadius(10)
            .foregroundColor(.white)
            .addVerifiedBadge(eventIsVerified)
    }
}
```

View modifiers often wrap the current view within yet another view, which is why we can get completely different layout results depending on which order that we call our modifiers in.


### Split multiple text block evenly
To make that happen, let’s give the Text within our EventInfoBadge an infinite max width — which will make the layout system scale it as much as possible on the horizontal axis before splitting it up into multiple lines:
```swift
struct EventInfoBadge: View {
    var iconName: String
    var text: String

    var body: some View {
        VStack {
            Image(systemName: iconName)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: 25, height: 25)
            Text(text)
                .frame(maxWidth: .infinity)
                .multilineTextAlignment(.center)
        }
        .padding(.vertical, 10)
        .padding(.horizontal, 5)
        .background(Color.secondary)
        .cornerRadius(10)
    }
}
```
