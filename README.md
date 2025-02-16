# ft_Transcendence : Pong Contest Website Project

## Table of Contents
- [Introduction](#introduction)
- [General Guidelines](#general-guidelines)
- [Overview](#overview)
- [Minimal Technical Requirements](#minimal-technical-requirements)
- [Game](#game)
- [Security Concerns](#security-concerns)
- [Modules](#modules)
  - [Web](#web)
  - [User Management](#user-management)
  - [Gameplay and User Experience](#gameplay-and-user-experience)
  - [Cybersecurity](#cybersecurity)
  - [Accessibility](#accessibility)

## Introduction
This project is about creating a website for the mighty Pong contest! The use of libraries or tools that provide an immediate and complete solution for a global feature or a module is prohibited.

## General Guidelines
- Any direct instruction about the usage (can, must, can’t) of a third-party library or tool must be followed.
- The use of a small library or tool that solves a simple and unique task, representing a subcomponent of a global feature or module, is allowed.
- During the evaluation, the team will justify any usage of a library or tool that is not explicitly approved by the subject and that is not in contradiction with the constraints of the subject.
- During the evaluation, the evaluator will take her/his responsibility and define if the usage of a specific library or tool is legitimate (and allowed) or almost solving an entire feature or module (and prohibited).

## Overview
Thanks to your website, users will play Pong with others. You have to provide a nice user interface and real-time multiplayer online games!

## Minimal Technical Requirements
Your project has to comply with the following rules:
- You are free to develop the site, with or without a backend.
  - If you choose to include a backend, it must be written in pure Ruby. However, this requirement can be overridden by the Framework module.
  - If your backend or framework uses a database, you must follow the constraints of the Database module.
- The frontend should be developed using pure vanilla JavaScript. However, this requirement can be altered through the FrontEnd module.
- Your website must be a single-page application. The user should be able to use the Back and Forward buttons of the browser.
- Your website must be compatible with the latest stable up-to-date version of Google Chrome.
- The user should encounter no unhandled errors and no warnings when browsing the website.
- Everything must be launched with a single command line to run an autonomous container provided by Docker. Example: `docker-compose up --build`

## Game
The main purpose of this website is to play Pong versus other players.
-Therefore, users must have the ability to participate in a live Pong game against another player directly on the website. Both players will use the same keyboard.The Remote players module can enhance this functionality with remote players.
- A player must be able to play against another player, but it should also be possible to propose a tournament. This tournament will consist of multiple players who can take turns playing against each other. You have flexibility in how you implement the tournament, but it must clearly display who is playing against whom and the order of the players.
- A registration system is required: at the start of a tournament, each player must input their alias name. The aliases will be reset when a new tournament begins. However, this requirement can be modified using the Standard User Management module.
- There must be a matchmaking system: the tournament system organizes the matchmaking of the participants and announces the next match.
- All players must adhere to the same rules, including having identical paddle speed. This requirement also applies when using AI; the AI must exhibit the same speed as a regular player.
- The game itself must be developed in accordance with the default frontend constraints, or you may choose to utilize the FrontEnd module, or override it with the Graphics module. While the visual aesthetics can vary, it must still capture the essence of the original Pong (1972).
  - The use of libraries or tools that provide an immediate and complete solution for a global feature or a module is prohibited.
  - Any direct instruction about the usage (can, must, can’t) of a third-party library or tool must be followed.
  - The use of a small library or tool that solves a simple and unique task, representing a subcomponent of a global feature or module, is allowed. 

## Security Concerns
To create a basic functional website, here are a few security concerns that you have to tackle:
- Any password stored in your database, if applicable, must be hashed.
- Your website must be protected against SQL injections/XSS.
- If you have a backend or any other features, it is mandatory to enable an HTTPS connection for all aspects.
- You must implement some form of validation for forms and any user input, either within the base page if no backend is used or on the server side if a backend is employed.
- Regardless of whether you choose to implement the JWT Security module with 2FA, it’s crucial to prioritize the security of your website. For instance, if you opt to create an API, ensure your routes are protected. Remember, even if you decide not to use JWT tokens, securing the site remains essential.

## Modules

### Web
These modules enable the integration of advanced web features into your Pong game.
- Use a Framework to build the backend.
  - In this major module, you are required to utilize a specific web framework for your backend development, and that framework is Django ..
  - You can create the backend without using the constraints of this module by using the default language/framework (see above in the mandatory part). However, this module will only be valid if you follow its requirements.
- Use a framework or a toolkit to build the frontend.
  - Your frontend development must use the Bootstrap toolkit in addition of the vanilla Javascript, and nothing else.
  - You can create a front-end without using the constraints of this module by using the default front-end directives (see above in the mandatory part). However, this module will only be valid if you follow its requirements.
- Use a database for the backend - and more. The designated database is PostgreSQL.
  - The designated database for all DB instances in your project is PostgreSQL . This choice guarantees data consistency and compatibility across all project components and may be a prerequisite for other modules, such as the backend Framework module.

### User Management
This module delves into the realm of User Management, addressing crucial aspects of user interactions and access control within the Pong platform. It encompasses two major components, each focused on essential elements of user management and authentication: user participation across multiple tournaments and the implementation of remote authentication.
- Standard user management, authentication, users across tournaments.
  - Users can subscribe to the website in a secure way.
  - Registered users can log in in a secure way.
  - Users can select a unique display name to play the tournaments.
  - Users can update their information.
  - Users can upload an avatar, with a default option if none is provided.
  - Users can add others as friends and view their online status.
  - User profiles display stats, such as wins and losses.
  - Each user has a Match History including 1v1 games, dates, and relevant details, accessible to logged-in users.
    - Be carefull, the management of duplicate usernames/emails is at your discretion. You must provide a solution that makes sense. 

### Gameplay and User Experience
These modules are designed to enhance the general gameplay of the project.
- Remote players
  - It is possible to have two distant players. Each player is located on a separated computer, accessing the same website and playing the same Pong game.
- Game Customization Options
- In this minor module, the goal is to provide customization options for all available games on the platform. Key features and objectives include:
  - Offer customization features, such as power-ups, attacks, or different maps,that enhance the gameplay experience.
  - Allow users to choose a default version of the game with basic features if they prefer a simpler experience.
  - Ensure that customization options are available and applicable to all games offered on the platform.
  - Implement user-friendly settings menus or interfaces for adjusting game parameters.
  - Maintain consistency in customization features across all games to provide a unified user experience.
### Cybersecurity
These cybersecurity modules are designed to bolster the security posture of the project, with the major module focusing on robust protection through Web Application Firewall (WAF) and ModSecurity configurations and HashiCorp Vault for secure secrets management. The minor modules complement this effort by adding options for GDPR compliance, user data anonymization, a ccount deletion, two-factor authentication (2FA), and JSON Web Tokens (JWT), collectively ensuring the project’s commitment to data protection, privacy, and authentication security.
- GDPR Compliance Options with User Anonymization, Local Data Management, and Account Deletion
  In this minor module, the goal is to introduce GDPR compliance options that allow users to exercise their data privacy rights. Key features and objectives include:
  - Implement GDPR-compliant features that enable users to request anonymization of their personal data, ensuring that their identity and sensitive information are protected.
  - Provide tools for users to manage their local data, including the ability to view, edit, or delete their personal information stored within the system.
  - Offer a streamlined process for users to request the permanent deletion of their accounts, including all associated data, ensuring compliance with data protection regulations.
  - Maintain clear and transparent communication with users regarding their data privacy rights, with easily accessible options to exercise these rights.
This minor module aims to enhance user privacy and data protection by offering GDPR compliance options that empower users to control their personal information and exercise their data privacy rights within the system. If you are not familiar with the General Data Protection Regulation (GDPR), it is essential to understand its principles and implications, especially regarding user data management and privacy. The GDPR is a regulation that aims to protect the personal data and privacy of individuals within the European Union (EU) and the European Economic Area (EEA). It sets out strict rules and guidelines for organizations on how they should handle and process personal data.

To gain a better understanding of the GDPR and its requirements, it is highly recommended to visit the official website of the European Commission on data protection(1) This website provides comprehensive information about the GDPR, including its principles, objectives, and user rights. It also offers additional resources to delve deeper into the topic and ensure compliance with the regulation.


If you are unfamiliar with the GDPR, please take the time to visit the provided link and familiarize yourself with the regulations before proceeding with this project.
    - 1 : [https://commission.europa.eu/law/law-topic/data-protection/legal-framework-eu-data-protection_en]
- Major module: Implement Two-Factor Authentication (2FA) and JWT.
  - In this major module, the goal is to enhance security and user authentication by introducing Two-Factor Authentication (2FA) and utilizing JSON Web Tokens (JWT). Key features and objectives include:
    - Implement Two-Factor Authentication (2FA) as an additional layer of security for user accounts, requiring users to provide a secondary verification method, such as a one-time code, in addition to their password.
    - Utilize JSON Web Tokens (JWT) as a secure method for authentication and authorization, ensuring that user sessions and access to resources are managed securely.
    - Provide a user-friendly setup process for enabling 2FA, with options for SMS codes, authenticator apps, or email-based verification.
    - Ensure that JWT tokens are issued and validated securely to prevent unauthorized access to user accounts and sensitive data.

### Accessibility
These modules are designed to enhance the accessibility of our web application, with a focus on ensuring compatibility across all devices, expanding browser support, offering multi-language capabilities, providing accessibility features for visually impaired users, and integrating Server-Side Rendering (SSR) for improved performance and user experience.
- Support on all devices.
  - Ensure that your website is responsive, adapting to different screen sizes and orientations.
- Minor module: Expanding Browser Compatibility.
  - Extend browser support to include an additional web browser.
