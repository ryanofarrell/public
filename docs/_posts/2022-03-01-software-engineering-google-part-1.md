---
layout: single
title:  "Learnings from Software Engineering at Google, part 1: What is Software Engineering?"
date:   2022-03-01 06:15:00 -0400
categories: posts
tags:
    - organizational effectiveness
    - leadership
    - software engineering
excerpt: "This post abstracts the software engineering principles and best practices used at Google into learnings that can be applied to all domains. Part 1 looks at chapter 1 of the book: What is Software Engineering?"
classes: wide

---

{% include figure 
    image_path="https://images-na.ssl-images-amazon.com/images/I/41uvuuFt06S._SX379_BO1,204,203,200_.jpg" 
    alt="SWE at Google" 
    class="align-right"
%}

This post is part 1 of an unknown number of posts I make while reading [“Software Engineering at Google: Lessons Learned from Programming Over Time”](https://www.amazon.com/Software-Engineering-Google-Lessons-Programming/dp/1492082791/ref=sr_1_1?keywords=software+engineering+at+google&qid=1645999024&sr=8-1). It will be based on a hybrid of the best practices from the book with my own knowledge, and will be applicable primarily to non-software engineers (sorry SWEs, you can just read the book).



## The parallels between software engineering and your job

The fundamental goal of a software engineer (SWE) or team of SWEs is to create software that produces value for their customers. The key point is that a software engineer’s Product is software but their end state is being a **value-add to their customers**. The *engineering* portion of software engineering relates to the culture, processes, and tools to deliver the software (deliver the value).

There are probably a multitude of ways you deliver value to your customers: for the sake of this post (and subsequent posts) I will address these methods of value-delivery as your capital-p **Products**. These Products are all the things you do and deliver that justify your existence in a company. And following the same logic as above, the culture, processes, and tools to deliver your Products can be considered the engineering portion of your job.

## Software engineering: Many people working together to produce, improve, and maintain *software* over time
The key distinction the book makes between programming and software engineering comes from two dimensions: duration and scalability

- The **duration** of a programming task is short; write code so that it runs, then move on. The duration of software engineering is long; write code that can exist, be improved, and be maintained over years, maybe decades
- There are no requirements on **scalability** of programming task; it can be localized to one person; software engineering requires team scalability in addition to technical scalability (infrastructure, CPUs, etc.); rarely will a software engineering task involve only one person

Because of these differences in duration and scalability, there are differences in the tools, processes, and culture required to best deliver value. You can no longer think just about issues from a programming lens; you must instead think about software engineering issues.

{% include figure 
    image_path="/assets/images/post-09/people-time-products.jpeg" 
    alt="All teams are people working on products over time" 
    class="align-left"
    caption="All teams are people working on products over time"
%}

## A non-technical version: Many people working together to produce, improve, and maintain Products over time
If we replace ‘software’ with the generic ‘Product’ described above, you can see how the problem sets significantly overlap. You and your teams face a very similar set of problems as software engineers:

- Your Products will have some usable lifespan, and over that time your Products will need to be improved, maintained, deprecated, discontinued, replaced, etc. How you engineer your Products will determine how challenging it is to manage that lifecycle.
- Your Products will be worked on by many different people over this time due to inevitable turnover on your team. The way your Products are engineered will have implications on how easily they scale across people.

Given overlapping problems, you can learn a lot about how to improve your Product/time/people relationships by studying the best practices of software engineering.

## Be cognizant of tradeoffs, especially speed vs scalability
Tradeoffs are inevitable, but you should be transparent in your decisions and strive for a culture where changing a decision due to new information is accepted as a best practice. One of the primary tradeoffs to think about between going fast and building for the future. Consider two teams addressing a need:

- Team 1 is focused only on getting the Product out the door, and therefore works in silos, does things manually, does not document how they got to outcomes, and is very dependent on one or two people
- Team 2 understand that the Product will need to be around for a few years, and spends time properly designing the Product, documents how to recreate key portions of the Product, cross-trains for skills sharing

{% include figure 
    image_path="/assets/images/post-09/tradeoffs.jpeg" 
    alt="tradeoffs" 
    class="align-right"
    caption="Be cognizant of the tradeoffs that exist when making decisions"
%}

There is not a universal ‘better option’; team 1’s approach likely works better in competitive first-to-market-wins environments, whereas team 2’s approach may very well scale more but they may miss the opportunity. One thing is for sure: team 1 will eventually be addressing issues in the future that they are neglecting today. This speed-vs-scalability tradeoff is one that must be made consciously, with the understanding that time must be allocated in the future pay down the cost of speed.


An often hidden cost of speed is the dependency on exceptional performance. “Go fast” is often used synonymously with “work harder” or “work more hours”, but [reliance on exceptionality is not a sustainable model for teams]({% post_url 2021-02-02-outcomes-are-random %}). It is best to ensure there are processes to promote sustainable pace, rather than an always-go-full-speed mentality.

## Who is responsible for scalability?

Incentives are usually a great way to predict behavior, therefore leadership is responsible for the culture of scalability. Scalability looks different in different domains, so consider the following pattern: a team member creates a custom, high-visibility Product on a regular cadence. This person is very good at their job and enjoys creating this Product. 

Is this team member incentivized to teach other people how to create this Product? **No**. Are they incentivized to document their process? **No**. Purely from a work-output standpoint, their value to the company is inversely related to the number of people who can also do their job (basic supply and demand). They actually are incentivized to make their job appear more difficult in order to deter anyone from learning it.

It falls on leadership to address these incentive problems. Some ways of doing this: 

- mandatory cross training on all key Products
- Product whiteboard sessions (equivalent to a code review, where the Product and its creation process are reviewed by the team for simplicity/accuracy)
- promoting knowledge sharing (creating the culture)
- including ‘sustainability of Product’ as an evaluation metric

All of these create a top-down incentive for team members to create scalable Products.

## Key takeaways

- Software engineering differs from programming in the added dimensionality of time and people
- Your organization also must consider the dimensions of time and people when building your Products
- All tradeoffs should be consciously addresses, especially the tradeoffs between speed and scalability
- Leadership is responsible for incentivizing scalability