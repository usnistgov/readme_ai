

<DESCRIPTION>
The Hedgehog library is a C++ library developed by NIST for creating parallel computations on heterogeneous nodes.
</DESCRIPTION>



<INSTRUCTIONS>
Use this library to create code for parallel computations
</INSTRUCTIONS>



<API>

<file1>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_ABSTRACT_EXECUTION_PIPELINE_H
#define HEDGEHOG_ABSTRACT_EXECUTION_PIPELINE_H

#include "../graph/graph.h"
#include "../../behavior/copyable.h"
#include "../../core/nodes/core_execution_pipeline.h"
#include "../../behavior/switch/multi_switch_rules.h"

/// @brief Hedgehog main namespace
namespace hh {

/// Execution pipeline abstraction
/// @brief Duplicate a graph with the same input and output types and associate each of the duplicates to a specified
/// device id (GPU). If none is provided, the devices are generated in sequence (for 3 duplicates, 4 graphs total, the
/// device ids are 0,1,2,3).
/// When implementing, the switch rules need to be provided. They are used to redirect an input data sent to the
/// execution pipeline to a specific graph. Each of the graphs inside an execution pipeline has an id (generated in
/// sequence) used to discriminate the graphs in the switch rules.
/// If the Execution pipeline is duplicated (because it is part of a graph which is also in another execution pipeline),
/// the copy method needs to be implemented.
/// @code
/// // Implementation of an execution pipeline that accepts int, float and double data and produces int, float and double data.
/// class IntFloatDoubleExecutionPipeline
///    : public hh::AbstractExecutionPipeline<3, int, float, double, int, float, double> {
/// public:
///  IntFloatDoubleExecutionPipeline(std::shared_ptr<hh::Graph<3, int, float, double, int, float, double>> const &graph,
///                                  size_t const &numberGraphs)
///      : hh::AbstractExecutionPipeline<3, int, float, double, int, float, double>(graph, numberGraphs) {}
///
///  ~IntFloatDoubleExecutionPipeline() override = default;
///
///  bool sendToGraph(std::shared_ptr<int> &data, size_t const &graphId) override {
///    // Return true of false if the int data needs to be sent to the graph of id graphId
///  }
///
///  bool sendToGraph(std::shared_ptr<float> &data, size_t const &graphId) override {
///    // Return true of false if the float data needs to be sent to the graph of id graphId
///  }
///
///  bool sendToGraph(std::shared_ptr<double> &data, size_t const &graphId) override {
///    // Return true of false if the double data needs to be sent to the graph of id graphId
///  }
///};
/// // Instantiate a graph and the execution pipeline
///  auto insideGraph = std::make_shared<hh::Graph<3, int, float, double, int, float, double>>();
///  auto innerInputInt = std::make_shared<IntFloatDoubleTask>();
///  auto innerTaskFloat = std::make_shared<IntFloatDoubleTask>();
///  auto innerOutput = std::make_shared<IntFloatDoubleTask>();
///  auto innerSM = std::make_shared<hh::StateManager<1, int, int>>(std::make_shared<IntState>());
///  auto innerGraph = std::make_shared<IntFloatDoubleGraph>();
///
/// // Create a graph
///  insideGraph->input<int>(innerInputInt);
///  insideGraph->input<float>(innerTaskFloat);
///  insideGraph->inputs(innerSM);
///  insideGraph->inputs(innerGraph);
///
///  insideGraph->edges(innerInputInt, innerOutput);
///  insideGraph->edges(innerSM, innerOutput);
///  insideGraph->edges(innerTaskFloat, innerOutput);
///  insideGraph->outputs(innerOutput);
///  insideGraph->outputs(innerGraph);
///
///  auto ep = std::make_shared<IntFloatDoubleExecutionPipeline>(insideGraph, 5);
/// @endcode
/// @attention The duplicated graph needs to be totally created before set to an execution pipeline, it won't be
/// modifiable thereafter.
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
class AbstractExecutionPipeline
    : public behavior::Node,
      public behavior::Copyable<AbstractExecutionPipeline<Separator, AllTypes...>>,
      public tool::BehaviorMultiReceiversTypeDeducer_t<tool::Inputs<Separator, AllTypes...>>,
      public tool::BehaviorMultiSwitchRulesTypeDeducer_t<tool::Inputs<Separator, AllTypes...>>,
      public tool::BehaviorMultiSendersTypeDeducer_t<tool::Outputs<Separator, AllTypes...>> {
#ifndef DOXYGEN_SHOULD_SKIP_THIS
  /// @brief Declare core::CoreExecutionPipeline as friend
  friend hh::core::CoreExecutionPipeline<Separator, AllTypes...>;
#endif //DOXYGEN_SHOULD_SKIP_THIS
 private:
  std::shared_ptr<Graph<Separator, AllTypes...>>
      graph_ = nullptr; ///< Original Graph that will be duplicated

  std::shared_ptr<core::CoreExecutionPipeline<Separator, AllTypes...>> const
      coreExecutionPipeline_ = nullptr; ///< Execution Pipeline core
 public:
  /// Create an execution pipeline that duplicates a @p graph, @p numberGraphs - 1 times. The graph id and the device id
  /// associated to each graph are generated in sequence. The given name is "Execution pipeline" by default.
  /// @param graph Graph to duplicate
  /// @param numberGraphs Number of graph in total in the execution pipeline
  /// @param name Name of the execution pipeline
  AbstractExecutionPipeline(
      std::shared_ptr<Graph<Separator, AllTypes...>> const graph,
      size_t const &numberGraphs,
      std::string const name = "Execution pipeline")
      : behavior::Node(
      static_cast<std::shared_ptr<core::abstraction::NodeAbstraction>>(
          static_cast<std::shared_ptr<core::abstraction::NodeAbstraction> const>(
              std::make_shared<core::CoreExecutionPipeline<Separator, AllTypes...>>(
                  this, graph->coreGraph_, numberGraphs, name)))
  ),
        behavior::Copyable<AbstractExecutionPipeline<Separator, AllTypes...>>(1),
        graph_(graph),
        coreExecutionPipeline_(std::dynamic_pointer_cast<core::CoreExecutionPipeline<Separator,
                                                                                     AllTypes...>>(this->core())) {}

  /// Create an execution pipeline from a graph and the given device ids. If there are n device ids given, the graph
  /// will be duplicated n-1 times (for a total of n graphs), and each device ids will be associated to each graph.
  /// The given name is "Execution pipeline" by default.
  /// @param graph Graph to duplicate
  /// @param deviceIds Vector of device ids associated to the graphs in the execution pipeline
  /// @param name Name of the execution pipeline
  AbstractExecutionPipeline(
      std::shared_ptr<Graph<Separator, AllTypes...>> const graph,
      std::vector<int> const &deviceIds,
      std::string const name = "Execution pipeline")
      : behavior::Node(
      std::make_shared<core::CoreExecutionPipeline<Separator, AllTypes...>>(this, graph->coreGraph_, deviceIds, name)
  ),
        behavior::Copyable<AbstractExecutionPipeline<Separator, AllTypes...>>(1),
        graph_(graph),
        coreExecutionPipeline_(std::dynamic_pointer_cast<core::CoreExecutionPipeline<Separator,
                                                                                     AllTypes...>>(this->core())) {}

  /// Default destructor
  ~AbstractExecutionPipeline() override = default;

 private:
  /// Accessor to the base graph
  /// @return The base Graph
  std::shared_ptr<Graph<Separator, AllTypes...>> const &graph() const { return graph_; }

  /// @brief graph setter
  /// @param graph Graph to set
  void graph(std::shared_ptr<Graph<Separator, AllTypes...>> graph) { graph_ = graph; }
};

}

#endif //HEDGEHOG_ABSTRACT_EXECUTION_PIPELINE_H
</file1>

<file2>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.



#ifndef HEDGEHOG_DEFAULT_SCHEDULER_H
#define HEDGEHOG_DEFAULT_SCHEDULER_H

#include <thread>
#include <sstream>
#include <vector>

#include "scheduler.h"
#include "../../core/abstractions/base/node/task_node_abstraction.h"
#include "../../core/abstractions/base/node/execution_pipeline_node_abstraction.h"
#include "../../core/abstractions/base/node/graph_node_abstraction.h"

/// @brief Hedgehog main namespace
namespace hh {

/// Default scheduler use in Hedgehog graph
/// @brief By default, each node that needs a thread gets a thread and management of these threads is left to the OS.
class DefaultScheduler : public Scheduler {
 private:
  std::unique_ptr<std::vector<std::thread>> const
      threads_ = nullptr; ///< Vector of threads for the graph nodes

  std::unique_ptr<std::vector<core::abstraction::GraphNodeAbstraction *>>
      innerGraphs_ = nullptr; ///< Scheduler's graph

 public:
  /// Default constructor
  DefaultScheduler() :
      threads_(std::make_unique<std::vector<std::thread>>()),
      innerGraphs_(std::make_unique<std::vector<core::abstraction::GraphNodeAbstraction *>>()) {}

  /// Default destructor
  ~DefaultScheduler() override = default;

  /// @brief Definition of virtual constructor
  /// @return New instance of DefaultScheduler
  [[nodiscard]] std::unique_ptr<Scheduler> create() const override { return std::make_unique<DefaultScheduler>(); }

  /// @brief Spawn the threads for all graph's nodes
  /// @param cores Graph's inside nodes
  /// @param waitForInitialization Wait for internal nodes to be initialized flags
  /// @throw std::runtime_error if a thread cannot be created, or if the core is malformed
  void spawnThreads(std::set<core::abstraction::NodeAbstraction *> const &cores, bool waitForInitialization) override {
    std::vector<core::abstraction::TaskNodeAbstraction *> taskExec{};

    for (auto &core : cores) {
      if (auto exec = dynamic_cast<core::abstraction::TaskNodeAbstraction *>(core)) {
        try {
          threads_->emplace_back(&core::abstraction::TaskNodeAbstraction::run, exec);
          taskExec.push_back(exec);
        } catch (std::exception const &e) {
          std::ostringstream oss;
          oss << "Can not create thread for node \"" << core->name() << "\" because of error: " << e.what();
          throw std::runtime_error(oss.str());
        }
      } else if (auto graph = dynamic_cast<core::abstraction::GraphNodeAbstraction *>(core)) {
        innerGraphs_->push_back(graph);
      } else {
        std::ostringstream oss;
        oss
            << "Node " << core->name() << "/" << core->id()
            << " does not derive from the right abstraction to be handled properly by the default scheduler.";
        throw std::runtime_error(oss.str());
      }
    }

    /// If asked, wait for all internals to be initialized before returning
    if (waitForInitialization) {
      while (!std::all_of(taskExec.cbegin(), taskExec.cend(),
                          [](auto const &exec) { return exec->isInitialized(); })) {}
    }

  }

  /// Wait for all inside nodes to join and join the threads of all inside graphs
  void joinAll() override {
    std::for_each(threads_->begin(), threads_->end(), [](std::thread &t) {  t.join(); });
    for (core::abstraction::GraphNodeAbstraction *innerGraph : *(this->innerGraphs_)) {
      innerGraph->joinThreads();
    }
  }

};
}

#endif //HEDGEHOG_DEFAULT_SCHEDULER_H
</file2>

<file3>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_GRAPH_H
#define HEDGEHOG_GRAPH_H

#include <ostream>
#include <filesystem>

#include "../../behavior/node.h"
#include "../../behavior/copyable.h"
#include "../../behavior/input_output/multi_senders.h"
#include "../../behavior/input_output/multi_receivers.h"

#include "../../core/nodes/core_graph.h"
#include "../printer/options/color_scheme.h"
#include "../printer/options/structure_options.h"
#include "../printer/options/debug_options.h"
#include "../printer/dot_printer.h"
#include "../printer/color/jet_color.h"
#include "../printer/color/blue_to_red_color.h"
#include "result_visitor.h"
#include "../printer/hedgehog_export_file.h"

/// @brief Hedgehog main namespace
namespace hh {

#ifndef DOXYGEN_SHOULD_SKIP_THIS
/// Abstract Execution Pipeline forward declaration
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
class AbstractExecutionPipeline;
#endif //DOXYGEN_SHOULD_SKIP_THIS

/// Hedgehog graph abstraction.
/// @brief The graph in the Hedgehog library allows the user to create a dataflow. The graph regroups a set of nodes
/// representing parts of the computation. The most important nodes are the tasks (for heavy computation), the state
/// managers (to manage the local state of the computation) and the graph themselves (nested computation).
///
/// If a node is set as input of the graph (Graph::input / Graph::inputs), the data sent to the graph are transmitted to
/// the input nodes. The output nodes (set with Graph::output / Graph::outputs) produce the output data of the graph.
/// Between the input and the output nodes, the nodes need to be connected via edges(Graph::edge / Graph::edges).
///
/// A graph can be duplicated with ah hh::AbstractExecutionPipeline. Useful for mapping data across multiple devices (such as GPUs).
///
/// The difference between the singular and plural method (Graph::input / Graph::inputs, Graph::output / Graph::outputs,
/// Graph::edge / Graph::edges) is/are the type[s] used for the connection: if it is plural the connection is made for
/// all possible types, if it is singular the connection is only made for the user specified type.
///
/// The sequence of operations to use a graph are:
///     - Instantiate a graph [See example]
///     - Populate the graph [See example]
///     - Run the graph (Graph::executeGraph)
///     - Push data into the graph (Graph::pushData)
///     - Indicate that no more data will be pushed (Graph::finishPushingData)
///     - Gather output data with Graph::getBlockingResult can be put in a while loop, the function returns nullptr when the
/// graph is terminated (with Graph::finishPushingData) and all data have been processed.
///     - Wait for the graph to fully terminate (Graph::waitForTermination)
/// @code
/// // Instantiate a graph and its nodes
///  auto g = std::make_shared<hh::Graph<3, int, float, double, int, float, double>>();
///  auto innerInputInt = std::make_shared<IntFloatDoubleTask>();
///  auto innerTaskFloat = std::make_shared<IntFloatDoubleTask>();
///  auto innerOutput = std::make_shared<IntFloatDoubleTask>();
///  auto innerSM = std::make_shared<hh::StateManager<1, int, int>>(std::make_shared<IntState>());
///  auto innerGraph = std::make_shared<IntFloatDoubleGraph>();
///
/// // Create a graph
///  g->input<int>(innerInputInt);
///  g->input<float>(innerTaskFloat);
///  g->inputs(innerSM);
///  g->inputs(innerGraph);
///
///  g->edges(innerInputInt, innerOutput);
///  g->edges(innerSM, innerOutput);
///  g->edges(innerTaskFloat, innerOutput);
///  g->outputs(innerOutput);
///  g->outputs(innerGraph);
///
///  g->executeGraph(); // Execute the graph
///
///  // Push different types of data
///  for (int i = 0; i < 2000; ++i) {
///    g->pushData(std::make_shared<int>(i));
///    g->pushData(std::make_shared<float>(i));
///    g->pushData(std::make_shared<double>(i));
///  }
///
///  // Indicate that no other data will be pushed (trigger termination of the graph)
///  g->finishPushingData();
///
///  // Get the output data
///  while (auto variant = g->getBlockingResult()) {
///    std::visit(hh::ResultVisitor{
///        [](std::shared_ptr<int> &val) { /*Do something with an int*/ },
///        [](std::shared_ptr<float> &val) { /*Do something else with a float*/ },
///        [](std::shared_ptr<double> &val) { /*Do something else again with a double*/ }
///      }, *variant);
///  }
///
///  // Wait for the graph to terminate
///  g->waitForTermination();
/// @endcode
/// The default scheduling method for a graph is to launch all the node's threads and let the OS manages the threads.
/// @attention The conformity rules are: 1) for the input nodes, the node and the graph should share at least one input
/// type, 2) for the output nodes, the node and the graph should share at least one output type and 3) between two nodes
/// an edge can only be drawn for [a] common type[s].
/// @attention If the process wants to push a certain amount of data / get the output and start with new input
/// data, the Graph::pushData and Graph::getBlockingResult can be alternated without the while loop because the graph
/// won't terminate. This technique can only be used if the number of output can be deduced in advance by the end user.
/// Once all processing is complete, then the user must indicate they are done with Graph::finishPushingData, otherwise
/// the graph will deadlock and never terminate.
/// The Graph::cleanGraph method can be used to "clean" the graph nodes, and reset the user nodes attributes between
/// computations.
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
class Graph :
    public behavior::Node,
    public tool::BehaviorMultiReceiversTypeDeducer_t<tool::Inputs<Separator, AllTypes...>>,
    public tool::BehaviorMultiSendersTypeDeducer_t<tool::Outputs<Separator, AllTypes...>> {
 private:
#ifndef DOXYGEN_SHOULD_SKIP_THIS
  /// @brief Declare CoreExecutionPipeline as friend
  friend core::CoreExecutionPipeline<Separator, AllTypes...>;
  /// @brief Declare AbstractExecutionPipeline as friend
  friend AbstractExecutionPipeline<Separator, AllTypes...>;
#endif //DOXYGEN_SHOULD_SKIP_THIS

  std::shared_ptr<core::CoreGraph<Separator, AllTypes...>> const
      coreGraph_ = nullptr; ///< Core of the graph
  std::unique_ptr<std::set<std::shared_ptr<Node>>>
      nodes_ = nullptr; ///< Set of nodes given by the end user

 public:
  /// Default graph constructor, construct a graph with the name "Graph" and with a default scheduler.
  /// @param name Name of the graph to construct
  /// @param scheduler Scheduler used by the graph (should inherit from hh::Scheduler)
  /// @throw std::runtime_error if the core is not valid, should derives from CoreGraph
  explicit Graph(
      std::string const &name = "Graph",
      std::unique_ptr<Scheduler> scheduler = std::make_unique<DefaultScheduler>()) :
      behavior::Node(std::make_unique<core::CoreGraph<Separator, AllTypes...>>(name, std::move(scheduler), this)),
      coreGraph_(std::dynamic_pointer_cast<core::CoreGraph<Separator, AllTypes...>>(this->core())),
      nodes_(std::make_unique<std::set<std::shared_ptr<Node>>>()) {
    if (coreGraph_ == nullptr) { throw std::runtime_error("The core used by the graph should be a CoreGraph."); }
  }

  /// Default graph destructor
  ~Graph() override = default;

  /// Set an input node and connect the node to the graph's inputs for all common types.
  /// @brief Check if the input node is a valid object, and then connect it to the graph for all common types.
  /// @tparam InputNode_t Type of the input node
  /// @param inputNode Input node to connect
  template<tool::CompatibleInputNode<typename core::GIM<Separator, AllTypes...>::inputs_t> InputNode_t>
  void inputs(std::shared_ptr<InputNode_t> inputNode) {
    auto node = std::static_pointer_cast<Node>(inputNode);
    // Store shared_ptr in case user dereference it while it is still needed
    nodes_->insert(node);
    this->coreGraph_->template setInputForAllCommonTypes<typename InputNode_t::inputs_t>(node->core().get());
  }

  /// Set an input node and connect the node to the graph's input InputDataType.
  /// @brief Check if the input node is a valid object, and then connect it to the graph input for the InputDataType type.
  /// @tparam InputDataType Input type used for the connection between the node and the graph
  /// @tparam InputNode_t Type of the input node
  /// @param inputNode Input node to connect
  template<
      class InputDataType,
      tool::CompatibleInputNodeForAType<InputDataType,
                                        typename core::GIM<Separator, AllTypes...>::inputs_t> InputNode_t>
  void input(std::shared_ptr<InputNode_t> inputNode) {
    auto node = std::static_pointer_cast<Node>(inputNode);
    // Store shared_ptr in case user dereference it while it is still needed
    nodes_->insert(node);
    this->coreGraph_->template setInputForACommonType<InputDataType,
                                                      typename InputNode_t::inputs_t>(node->core().get());
  }

  /// Set an output node and connect the node to the graph's outputs for all common types.
  /// @brief Check if the output node is a valid object, and then connect it to the graph output for all common types.
  /// @tparam OutputNode_t Type of the output node
  /// @param outputNode Output node to connect
  template<tool::CompatibleOutputNode<typename core::GOM<Separator, AllTypes...>::outputs_t> OutputNode_t>
  void outputs(std::shared_ptr<OutputNode_t> outputNode) {
    auto node = std::static_pointer_cast<Node>(outputNode);
    // Store shared_ptr in case user dereference it while it is still needed
    nodes_->insert(node);

    this->coreGraph_->template setOutputForAllCommonTypes<typename OutputNode_t::outputs_t>(node->core().get());
  }

  /// Set an output node and connect the node to the graph's output OutputDataType.
  /// @brief Check if the output node is a valid object, and then connect it to the graph output for the OutputDataType type.
  /// @tparam OutputDataType Output type used for the connection between the node and the graph
  /// @tparam OutputNode_t Type of the output node
  /// @param outputNode Output node to connect
  template<class OutputType,
      tool::CompatibleOutputNodeForAType<OutputType,
                                         typename core::GOM<Separator, AllTypes...>::outputs_t> OutputNode_t>
  void output(std::shared_ptr<OutputNode_t> outputNode) {
    auto node = std::static_pointer_cast<Node>(outputNode);
    // Store shared_ptr in case user dereference it while it is still needed
    nodes_->insert(node);
    this->coreGraph_->template setOutputForACommonType<OutputType,
                                                       typename OutputNode_t::outputs_t>(node->core().get());
  }

  /// Create an edge between two nodes for all common types
  /// @brief Validate the sender and receiver node and if valid, create an edge for all common types between the sender
  /// output types and the receiver input types
  /// @tparam SenderNode_t Type of the sender node
  /// @tparam ReceiverNode_t Type of the receiver node
  /// @param sender Sender node
  /// @param receiver Receiver node
  template<tool::SenderNode SenderNode_t, tool::ReceiverNode ReceiverNode_t>
  void edges(std::shared_ptr<SenderNode_t> sender, std::shared_ptr<ReceiverNode_t> receiver) {
    static_assert(
        std::tuple_size_v<
            tool::Intersect_t<typename SenderNode_t::outputs_t, typename ReceiverNode_t::inputs_t>
        > != 0, "The sender and the receiver nodes should at least share a type."
    );
    auto senderNode = std::static_pointer_cast<Node>(sender);
    auto receiverNode = std::static_pointer_cast<Node>(receiver);
    // Store shared_ptr in case user dereference it while it is still needed
    nodes_->insert(senderNode);
    nodes_->insert(receiverNode);

    this->coreGraph_
        ->template addEdgeForAllCommonTypes<typename SenderNode_t::outputs_t, typename ReceiverNode_t::inputs_t>
            (senderNode->core().get(), receiverNode->core().get());
  }

  /// Create an edge between two nodes for a specific type
  /// @brief Validate the sender and receiver node and if valid, create an edge for the CommonType type
  /// @tparam SenderNode_t Type of the sender node
  /// @tparam ReceiverNode_t Type of the receiver node
  /// @param sender Sender node
  /// @param receiver Receiver node
  template<class CommonType,
      tool::SenderNodeForAType<CommonType> SenderNode_t, tool::ReceiverNodeForAType<CommonType> ReceiverNode_t>
  void edge(std::shared_ptr<SenderNode_t> sender, std::shared_ptr<ReceiverNode_t> receiver) {
    auto senderNode = std::static_pointer_cast<Node>(sender);
    auto receiverNode = std::static_pointer_cast<Node>(receiver);
    // Store shared_ptr in case user dereference it while it is still needed
    nodes_->insert(senderNode);
    nodes_->insert(receiverNode);

    this->coreGraph_->template addEdgeForACommonType<
        CommonType,
        typename SenderNode_t::outputs_t, typename ReceiverNode_t::inputs_t>
        (senderNode->core().get(), receiverNode->core().get());
  }

  /// Execute the graph
  /// @brief Duplicate the nodes in a group and use the scheduler to associate threads to the nodes
  /// @param waitForInitialization Wait for internal nodes to be initialized flags [default = false]
  void executeGraph(bool waitForInitialization = false) { coreGraph_->executeGraph(waitForInitialization); }

  /// Indicate to the graph that no more input data are pushed to the graph
  /// @brief Trigger the termination of the graph, each nodes terminates in a cascaded when (by default) no predecessor
  /// node is connected to the node and the input node queues are empty.
  void finishPushingData() { coreGraph_->finishPushingData(); }

  /// Push data into the graph
  /// @details Each input data is sent to all input nodes that match the input type that is sent.
  /// @tparam CompatibleInputType_t Type on the input data
  /// @param data Data sent to the graph
  template<tool::MatchInputTypeConcept<tool::Inputs<Separator, AllTypes...>> CompatibleInputType_t>
  void pushData(std::shared_ptr<CompatibleInputType_t> data) { this->coreGraph_->broadcastAndNotifyAllInputNodes(data); }

  /// Wait for the graph to terminate
  /// @brief A graph terminate when all the threads it manages are terminated (i.e. when all the nodes are terminated)
  void waitForTermination() { coreGraph_->waitForTermination(); }

  /// Get result data from the graph
  /// @brief Get result from the graph while blocking the main thread. The results are presented under the form of
  /// @code
  /// std::shared_ptr<std::variant<std::shared_ptr<Output1>, std::shared_ptr<Output2>, std::shared_ptr<Output3>>>
  /// @endcode
  /// If the output type is known in advance one can use
  /// @code
  /// std::get<std::shared_ptr<KnownType>>(*result)
  /// @endcode
  /// If multiple types are possible the following code can be used:
  /// @code
  /// std::visit(hh::ResultVisitor{
  ///     [](std::shared_ptr<Output1> &val) { /*Do something with an Output1*/ },
  ///     [](std::shared_ptr<Output2> &val) { /*Do something else with a Output2*/ },
  ///     [](std::shared_ptr<Output3> &val) { /*Do something else again with a Output3*/ }
  ///   }, *result);
  /// @endcode
  /// @return A result of the graph
  auto getBlockingResult() { return coreGraph_->getBlockingResult(); }

  /// Create a dot file representing a snapshot of the state of the graph at the moment of the call, the graph is
  /// saved into the file dotFilePath.
  /// @param dotFilePath Path where the file is stored.
  /// @param colorScheme Color scheme used to color the tasks, either to show difference in execution or in waiting
  /// times, or nothing. The chosen color depends on the colorPicker.
  /// @param structureOptions Show how the graph is represented, with or without input queue size, with or without all
  /// task groups.
  /// @param inputOption Select how the execution should be printed, by input type or gathered
  /// @param debugOption Add debug information on the dot graph.
  /// @param colorPicker Color scheme used to generate the dotfile, JetColor by default.
  /// @param verbose Enable verbose mode: report when dot files are created or overwritten to standard out, default
  /// false.
  void createDotFile(std::filesystem::path const &dotFilePath,
                     ColorScheme colorScheme = ColorScheme::NONE,
                     StructureOptions structureOptions = StructureOptions::NONE,
                     InputOptions inputOption = InputOptions::GATHERED,
                     DebugOptions debugOption = DebugOptions::NONE,
                     std::unique_ptr<ColorPicker> colorPicker = std::make_unique<JetColor>(),
                     bool verbose = false) {
    core::abstraction::GraphNodeAbstraction *core = this->coreGraph_.get();
    DotPrinter
        printer(
        std::filesystem::absolute(dotFilePath), colorScheme, structureOptions, inputOption, debugOption, core,
        std::move(colorPicker), verbose);
    core->visit(&printer);
  }

  /// @brief Set the device id (GPU ID) for all the nodes in a graph
  /// @param deviceId Device Id to set
  void deviceId(int deviceId) { this->coreGraph_->deviceId(deviceId); }

  /// @brief Clean the graph
  /// @brief Call in sequence the clean method in all internal nodes. May be use to reset the attributes of user nodes
  /// between computations.
  void cleanGraph() {
    this->coreGraph_->cleanGraph();
  }

  /// @brief Generate a read only hedgehog report file (graph name + .hhrojson) used in the GUI
  void generateHedgehogExportFile() const {
    core::abstraction::GraphNodeAbstraction *core = this->coreGraph_.get();
    HedgehogExportFile printer(core);
    core->visit(&printer);
  }
};
}

#endif //HEDGEHOG_GRAPH_H
</file3>

<file4>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of 
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_GRAPH_SIGNAL_HANDLER_H
#define HEDGEHOG_GRAPH_SIGNAL_HANDLER_H
#pragma  once

#include <csignal>
#include <cstring>

#include "graph.h"
/// @brief Hedgehog main namespace
namespace hh {
/// @brief Implements a signal handler to catch events such as termination and killing.
/// @details Once a signal is caught, all task graphs that are registered with the signal handler will be written as a
/// dot file. The dot file is output in the working directory with the name of the signal as a prefix and
/// '<#>-graph-output.dot' as the suffix. This can be used to help debug the graph and understand the state of the graph.
/// For example, if the graph is deadlocked and the kill signal is handled, then the graph will be saved when terminating
/// the program. Visualizing the graph can pinpoint the location of the deadlock.
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
class GraphSignalHandler {
 private:
  static hh::Graph<Separator, AllTypes...> *graphInstance_; ///<< The outer graph instance
  static bool signalHandled_; ///< Flag to indicate if a signal has been fired or not
  static hh::ColorScheme colorScheme_; ///<< The color scheme to use for graph dot file
  static hh::StructureOptions structureOptions_; ///<< The structure options to use for graph dot file
  static hh::DebugOptions debugOptions_; ///<< The debug options to use for graph dot file
  static hh::InputOptions inputOptions_; ///<< The input options to use for graph dot file

 public:
  /// @brief Function that handles signals.
  /// @details Use TaskGraphSignalHandler::registerSignal to signal to this function
  /// @attention This function is used by the signal handler that is registered from std::signal, and should not be
  /// called directly by the user.
  /// @param signum the signal number that was triggered
  static void handleSignal(int signum = SIGTERM) {
#ifdef _WIN32
    std::string signalString(std::to_string(signum));
#else
    std::string signalString(strsignal(signum));
#endif

    if (!signalHandled_) {
      signalHandled_ = true;
      std::cout << "signal caught: " << signum << ": (" << signalString << ")" << std::endl;
      graphInstance_->createDotFile(
          signalString + "-graph-output.dot", colorScheme_, structureOptions_, inputOptions_, debugOptions_);
    }
  }

  /// @brief Create a dot file at exit if the instance still exist
  static void atExit() { if (graphInstance_) { graphInstance_->createDotFile("Exit-graph-output.dot"); } }

  /// @brief Sets the color scheme for dot file generation
  /// @param scheme the color scheme
  static void setColorScheme(hh::ColorScheme scheme) { colorScheme_ = scheme; }

  /// @brief Sets the structure options for dot file generation
  /// @param options the structure options
  static void setStructureOptions(hh::StructureOptions options) { structureOptions_ = options; }

  /// @brief Sets the debug options for dot file generation
  /// @param options the debug options
  static void setDebugOptions(hh::DebugOptions options) { debugOptions_ = options; }

  /// @brief Sets the input options for dot file generation
  /// @param options the input options
  static void setInputOptions(hh::InputOptions options) { inputOptions_ = options; }

  /// @brief Registers a task graph to be displayed when a signal is fired.
  /// @param graph the task graph to be displayed.
  static void registerGraph(hh::Graph<Separator, AllTypes...> *graph) { graphInstance_ = graph; }

  /// @brief Registers a signal for handling. (default SIGTERM)
  /// @param signum Signal number id
  /// @param atExit Boolean to test if GraphSignalHandler::atExit is called
  static void registerSignal(int signum = SIGTERM, bool atExit = false) {
    std::signal(signum, GraphSignalHandler<Separator, AllTypes ...>::handleSignal);
    if (atExit) {
      std::atexit(GraphSignalHandler<Separator, AllTypes ...>::atExit);
    }
  }
};

/// @brief Set default value at false
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
bool GraphSignalHandler<Separator, AllTypes...>::signalHandled_ = false;

/// @brief Set default value at nullptr
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
hh::Graph<Separator, AllTypes...> *GraphSignalHandler<Separator, AllTypes...>::graphInstance_ = nullptr;

/// @brief Sets the default color scheme
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
hh::ColorScheme GraphSignalHandler<Separator, AllTypes...>::colorScheme_ = hh::ColorScheme::EXECUTION;

/// @brief Sets the default structure options
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
hh::StructureOptions GraphSignalHandler<Separator, AllTypes...>::structureOptions_ = hh::StructureOptions::ALL;

/// @brief Sets the default debug options
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
hh::DebugOptions GraphSignalHandler<Separator, AllTypes...>::debugOptions_ = hh::DebugOptions::ALL;

/// @brief Sets the default input options
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
hh::InputOptions GraphSignalHandler<Separator, AllTypes...>::inputOptions_ = hh::InputOptions::SEPARATED;
}

#endif //HEDGEHOG_GRAPH_SIGNAL_HANDLER_H
</file4>

<file5>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This sofaware is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_RESULT_VISITOR_H
#define HEDGEHOG_RESULT_VISITOR_H

/// @brief Hedgehog main namespace
namespace hh {

/// Visitor used to explore Hedgehog graph variant result
/// @tparam Ts Types contained in the variant
template<class... Ts>
struct ResultVisitor : Ts ... { using Ts::operator()...; };

/// @brief Helper to the visitor
template<class... Ts> ResultVisitor(Ts...) -> ResultVisitor<Ts...>;
}

#endif //HEDGEHOG_RESULT_VISITOR_H
</file5>

<file6>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_SCHEDULER_H
#define HEDGEHOG_SCHEDULER_H

#include <memory>
#include <set>

#include "../../core/abstractions/base/node/node_abstraction.h"
/// @brief Hedgehog main namespace
namespace hh {

/// @brief Scheduler abstraction to manage graph's threads
class Scheduler {

 public:
  /// @brief Scheduler default constructor
  Scheduler() = default;

  /// @brief Scheduler default destructor
  virtual ~Scheduler() = default;

  /// @brief Definition of virtual constructor
  /// @return New instance of Scheduler
  [[nodiscard]] virtual std::unique_ptr<Scheduler> create() const = 0;

  /// @brief Spawn the threads of a graph
  /// @param cores Cores of every nodes in a graph
  /// @param waitForInitialization Wait for internal nodes to be initialized flags
  virtual void spawnThreads(std::set<core::abstraction::NodeAbstraction *> const &cores, bool waitForInitialization) = 0;

  /// @brief Method waiting for all graph's threads termination, called when Graph::waitForTermination() is called
  virtual void joinAll() = 0;
};

}

#endif //HEDGEHOG_SCHEDULER_H
</file6>

<file7>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_MANAGED_MEMORY_H
#define HEDGEHOG_MANAGED_MEMORY_H

#pragma once

#include <memory>

#include "manager/abstract_memory_manager.h"

/// @brief Hedgehog main namespace
namespace hh {

/// @brief Abstraction used to manage an user type with a memory manager
class ManagedMemory : public std::enable_shared_from_this<ManagedMemory> {
 private:
  AbstractMemoryManager *memoryManager_ = nullptr; ///< Link to the Memory Manager
 public:
/// @brief Default constructor
  ManagedMemory() = default;

/// @brief Default destructor
  virtual ~ManagedMemory() = default;

/// @brief Test is a memory manager has been connected to the managed memory
/// @return True if a memory manager has been connected, else False
  bool isMemoryManagerConnected() { return memoryManager_ != nullptr; }

/// @brief Memory manager accessor
/// @return Memory manager
  [[nodiscard]] AbstractMemoryManager *memoryManager() const { return memoryManager_; }

/// @brief Memory manager setter
/// @param memoryManager Memory manager to set
  void memoryManager(AbstractMemoryManager *memoryManager) { memoryManager_ = memoryManager; }

  /// @brief Return the data to the memory manager
  /// @throw std::runtime_error if the data is not linked to a memory manager
  void returnToMemoryManager() {
    if (memoryManager_) {
      memoryManager_->recycleMemory(this->shared_from_this());
    } else {
      throw (std::runtime_error("The data you are trying to return is not linked to a memory manager."));
    }
  }

  /// @brief Mechanism called by Hedgehog when the node returns the memory before it is tested for being recycled (call to canBeRecycled)
  virtual void postProcess() {};

  /// @brief Accessor to test if the data can be cleaned and sent back to the Pool, true by default
  /// @return True if the data can be sent to the Pool, else False
  virtual bool canBeRecycled() { return true; }

  /// @brief Mechanism to clean data.
  /// @details If the ManagedMemory type uses user-defined allocations, then clean is an appropriate place to
  /// deallocate the user-allocated data. It will be called only once before it is sent back to the pool.
  /// @attention If a StaticMemoryManager is used, then deallocation should be done within the destructor to match
  /// any allocations done within the constructor. (see StaticMemoryManager for more details)
  virtual void clean() {};

  /// @brief Mechanism to pre process the data.
  /// @details If the ManagedMemory type uses user-defined allocations such as unified memory, then preProcess is an
  /// appropriate place to apply synchronization on any asynchronous operations that were applied in the clean
  /// function. It will be called only once before it is returned from getManagedMemory.
  virtual void preProcess() {};

};
}

#endif //HEDGEHOG_MANAGED_MEMORY_H
</file7>

<file8>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_POOL_H
#define HEDGEHOG_POOL_H

#pragma once

#include <deque>
#include <memory>
#include <sstream>
#include <condition_variable>

/// Hedgehog main namespace
namespace hh {
/// Hedgehog tool namespace
namespace tool {

/// @brief Pool of data used by the memory manager
/// @tparam T Type stored in the pool
template<class T>
class Pool {
 private:
  size_t const capacity_ = 1; ///< Capacity of the pool
  std::deque<std::shared_ptr<T>> queue_ = {}; ///< Actual storage used by the pool
  std::mutex mutex_ = {}; ///< Mutex used to protect the queue
  std::unique_ptr<std::condition_variable>
      conditionVariable_ = std::make_unique<std::condition_variable>(); ///< Condition variable to wake up a thread
                                                                        ///< waiting for data
 public:
  /// @brief Create a pool with a certain capacity
  /// @param capacity Pool's capacity
  explicit Pool(size_t const &capacity) : capacity_(capacity == 0 ? 1 : capacity) {
    queue_ = std::deque<std::shared_ptr<T >>(capacity_);
  }

  /// @brief Getter to the iterator to the beginning of the Pool
  /// @return Iterator to the beginning of the Pool
  typename std::deque<std::shared_ptr<T>>::iterator begin() { return this->queue_.begin(); }

  /// @brief Getter to the iterator to the end of the Pool
  /// @return Iterator to the end of the Pool
  typename std::deque<std::shared_ptr<T>>::iterator end() { return this->queue_.end(); }

  /// @brief Getter to the pool's size
  /// @return Pool size
  size_t size() {
    mutex_.lock();
    auto s = queue_.size();
    mutex_.unlock();
    return s;
  }

  /// @brief Returns true if the Pool is empty. (Thus begin() would equal end()).
  /// @return Returns true if the Pool is empty. (Thus begin() would equal end()).
  bool empty() {
    mutex_.lock();
    auto e = queue_.empty();
    mutex_.unlock();
    return e;
  }

  /// @brief Getter to the pool's capacity
  /// @return Pool capacity
  [[nodiscard]] size_t capacity() const { return capacity_; }

  /// @brief The function creates an element at the end of the pool and assigns the given data to it. Once inserted one
  /// waiting thread is woken up
  /// @param data Data to insert
  /// @throw std::runtime_error if the queue is overflowing
  void push_back(std::shared_ptr<T> const &data) {
    mutex_.lock();
    this->queue_.push_back(data);

    if (this->queue_.size() > capacity_) {
      std::ostringstream oss;
      oss << "The queue is overflowing, the same data " << data
          << " has been returned to the memory manager too many times: " << __FUNCTION__;
      throw (std::runtime_error(oss.str()));
    }
    mutex_.unlock();
    conditionVariable_->notify_one();
  }

  /// @brief Extract an element from the queue. If none is available wait until one become available
  /// @return Element from the queue
  std::shared_ptr<T> pop_front() {
    std::unique_lock<std::mutex> lock(mutex_);
    std::shared_ptr<T> ret = nullptr;
    conditionVariable_->wait(lock, [this]() { return !queue_.empty(); });
    ret = queue_.front();
    queue_.pop_front();
    return ret;
  }
};
}
}

#endif //HEDGEHOG_POOL_H
</file8>

<file9>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_ABSTRACT_MEMORY_MANAGER_H
#define HEDGEHOG_ABSTRACT_MEMORY_MANAGER_H

#pragma once

#include <memory>
#include <mutex>

#include "../pool.h"
#include "../../../tools/nvtx_profiler.h"

/// @brief Hedgehog main namespace
namespace hh {

#ifndef DOXYGEN_SHOULD_SKIP_THIS

/// Forward declaration of Managed Memory
class ManagedMemory;
#endif //DOXYGEN_SHOULD_SKIP_THIS

/// Abstract Memory manager
/// @brief Present a thread safe pool of Managed memory
class AbstractMemoryManager {
 private:
  int deviceId_ = 0; ///< Device Id of linked task
  bool initialized_ = false; ///< Flag to determine if AbstractMemoryManager has been initialized
  std::unique_ptr<tool::Pool<ManagedMemory>> pool_ = {}; ///< Inside pool to store the data
  std::shared_ptr<NvtxProfiler> profiler_ = nullptr; ///< NVTX profiler instance to follow memory manager state
 protected:
  std::mutex memoryManagerMutex_ = {}; ///< Mutex for user interface

 public:
  /// @brief Only used constructor
  /// @param capacity Memory Manager capacity, number of elements available, set to 1 if 0
  explicit AbstractMemoryManager(size_t const &capacity) :
      deviceId_(0),
      pool_(std::make_unique<tool::Pool<ManagedMemory>>(capacity > 0 ? capacity : 1)) {}

  /// @brief Default destructor
  virtual ~AbstractMemoryManager() = default;

  /// @brief Device Id accessor
  /// @return Device id
  [[nodiscard]] int deviceId() const { return deviceId_; }

  /// @brief Return the current size of the inside pool
  /// @details Lock the api user mutex before getting the current size of the inside pool
  /// @return The current number of available data
  [[nodiscard]] size_t currentSize() {
    memoryManagerMutex_.lock();
    auto s = this->pool()->size();
    memoryManagerMutex_.unlock();
    return s;
  }

  /// @brief Capacity accessor
  /// @return Pool's capacity
  [[nodiscard]] size_t capacity() const {
    return this->pool()->capacity();
  };

  /// @brief Device id setter
  /// @param deviceId Task's device id to set
  void deviceId(int deviceId) { deviceId_ = deviceId; }

  /// @brief NVTX profiler setter
  /// @param profiler NVTX profiler to set
  void profiler(const std::shared_ptr<NvtxProfiler> &profiler) { this->profiler_ = profiler; }

  /// @brief Get an available managed memory, block if none are available
  /// @return An available managed memory
  virtual std::shared_ptr<ManagedMemory> getManagedMemory() = 0;

  /// @brief Recycle memory
  /// @details Lock the user api mutex before call used(), canBeRecycled() and if true, clean() and push it back into
  /// the pool
  /// @param managedMemory Data to clean
  virtual void recycleMemory(std::shared_ptr<ManagedMemory> const &managedMemory) = 0;

  /// @brief Virtual copy method used for task duplication and execution pipeline
  /// @return Return a copy of this specialised AbstractMemoryManager
  virtual std::shared_ptr<AbstractMemoryManager> copy() = 0;

  /// @brief Initialize the memory manager
  /// @details Lock the user api mutex, fill the pool with default constructed data, and call initializeMemoryManager()
  virtual void initialize() = 0;

  /// @brief Return the real managed type under the form of a string
  /// @return Real managed type under the form of a string
  [[nodiscard]] virtual std::string managedType() const = 0;

 protected:
  /// @brief Accessor to NVTX profiler
  /// @return Attached NVTX profiler
  [[nodiscard]] std::shared_ptr<NvtxProfiler> const &profiler() const {
    return profiler_;
  }

  /// @brief Inside pool accessor
  /// @return Inside pool
  [[nodiscard]] std::unique_ptr<tool::Pool<ManagedMemory>> const &pool() const { return pool_; }

  /// @brief Initialized flag accessor
  /// @return True is the memory manager has been initialized, else False
  [[nodiscard]] bool isInitialized() const { return initialized_; }

  /// @brief User api mutex accessor
  /// @return User api mutex
  [[nodiscard]] std::mutex &memoryManagerMutex() { return memoryManagerMutex_; }

  /// @brief Flag the memory manager has initialized
  void initialized() { initialized_ = true; }
};
}

#endif //HEDGEHOG_ABSTRACT_MEMORY_MANAGER_H
</file9>

<file10>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_MEMORY_MANAGER_H
#define HEDGEHOG_MEMORY_MANAGER_H

#pragma once

#include "../managed_memory.h"
#include "abstract_memory_manager.h"
#include "../../../tools/concepts.h"

/// @brief Hedgehog main namespace
namespace hh {

/// Base memory manager
/// @brief Memory manager with default created managed object
/// @tparam T Type managed by the memory manager
template<tool::ManageableMemory T>
class MemoryManager : public AbstractMemoryManager {
 public:
  /// Create a memory manager with a certain capacity
  /// @param capacity Capacity of the memory manager
  explicit MemoryManager(size_t const &capacity) : AbstractMemoryManager(capacity) {}

  /// @brief Default destructor
  ~MemoryManager() override = default;

  /// Default copy method
  /// @attention Need to be overloaded by the end user if the memory manager is inherited
  /// @return Create another MemoryManager from this
  std::shared_ptr<AbstractMemoryManager> copy() override {
    return std::make_shared<MemoryManager>(this->capacity());
  }

  /// @brief User-definable initialization step for a memory manager
  virtual void initializeMemoryManager() {}

  /// Get managed memory from the pool
  /// @brief Get managed memory from the pool. If the pool is empty, the call will block until a new element get
  /// available.
  /// @return A managed memory
  std::shared_ptr<ManagedMemory> getManagedMemory() final   {
    std::shared_ptr<ManagedMemory> managedMemory = nullptr;
    managedMemory = this->pool()->pop_front();
    managedMemory->preProcess();
    return managedMemory;
  }

 private:
  /// Recycling mechanism for managed memory
  /// @brief Thread safe recycle that will in sequence:
  ///     - calls ManagedMemory::postProcess()
  ///     - if ManagedMemory::canBeRecycled() returns true
  ///     - calls ManagedMemory::clean()
  /// @param managedMemory Type of the managed memory
  void recycleMemory(std::shared_ptr<ManagedMemory> const &managedMemory) final {
    memoryManagerMutex_.lock();
    managedMemory->postProcess();
    if (managedMemory->canBeRecycled()) {
      this->profiler()->addReleaseMarker();
      managedMemory->clean();
      this->pool()->push_back(managedMemory);
    }
    memoryManagerMutex_.unlock();
  }

  /// Initialize the memory manager
  /// @brief Thread safe initialization, fill the pool with default constructed object
  void initialize() final {
    memoryManagerMutex_.lock();
    if (!this->isInitialized()) {
      this->initialized();
      std::for_each(
          this->pool()->begin(), this->pool()->end(),
          [this](std::shared_ptr<ManagedMemory> &emptyShared) {
            emptyShared = std::make_shared<T>();
            emptyShared->memoryManager(this);
          }
      );
      initializeMemoryManager();
    }
    memoryManagerMutex_.unlock();
  }

  /// Getter to real managed type as string
  /// @return String of the real managed type
  [[nodiscard]] std::string managedType() const final { return hh::tool::typeToStr<T>(); }
};
}

#endif //HEDGEHOG_MEMORY_MANAGER_H
</file10>

<file11>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_STATIC_MEMORY_MANAGER_H
#define HEDGEHOG_STATIC_MEMORY_MANAGER_H

#pragma once

#include "../managed_memory.h"
#include "abstract_memory_manager.h"

/// @brief Hedgehog main namespace
namespace hh {

/// Static memory manager
/// @brief Static Memory manager with custom created managed object. The type T managed has to present a constructor
/// with a signature that matches exactly the template argument list Args...
/// @tparam T Type managed
/// @tparam Args List of types that should match the constructor of T parameters
template<class T, class ...Args>
class StaticMemoryManager : public AbstractMemoryManager {
  static_assert(std::is_base_of_v<ManagedMemory, T>, "The type managed by the StaticMemoryManager should derive from hh::ManagedMemory.");
  static_assert(std::is_constructible_v<T, Args...>, "The type managed by the StaticMemoryManager should be constructible with Args type(s).");
 private:
  std::tuple<Args...> args_ = {}; ///< Values to pass to the constructor
 public:
  /// Constructor to a static memory manager.
  ///  @brief Construct a static memory manager from its capacity, and the arguments used to construct all elements
  /// in the pool.
  /// @param capacity Memory manager capacity
  /// @param args Arguments used to construct every elements in the pool
  explicit StaticMemoryManager(size_t const &capacity, Args ... args)
      : AbstractMemoryManager(capacity), args_(std::forward<Args>(args)...) {}

  /// @brief Copy constructor
  /// @param rhs StaticMemoryManager to construct from
  StaticMemoryManager(StaticMemoryManager<T, Args...> const & rhs)
      : AbstractMemoryManager(rhs.capacity()), args_(rhs.args_) {}

  /// @brief Default destructor
  ~StaticMemoryManager() override = default;

  /// Get a managed memory from the pool
  /// @brief Get a managed memory from the pool. If the pool is empty, the call will block until a new element get
  /// available.
  /// @return A managed memory
  std::shared_ptr<ManagedMemory> getManagedMemory() final {
    std::shared_ptr<ManagedMemory> managedMemory = nullptr;
    managedMemory = this->pool()->pop_front();
    managedMemory->preProcess();
    return managedMemory;
  }

  /// Default copy method
  /// @attention Need to be overloaded by the end user if the memory manager is inherited
  /// @return Create another MemoryManager from this
  std::shared_ptr<AbstractMemoryManager> copy() override {
    return std::make_shared<StaticMemoryManager<T, Args...>>(*this);
  }

  /// @brief User-definable initialization step for a memory manager
  virtual void initializeMemoryManager() {}

 private:
  /// Recycling mechanism for managed memory
  /// @brief Thread safe recycle that will in sequence:
  ///     - calls ManagedMemory::postProcess()
  ///     - if ManagedMemory::canBeRecycled() returns true
  ///     - calls ManagedMemory::clean()
  /// @param managedMemory Type of the managed memory
  void recycleMemory(std::shared_ptr<ManagedMemory> const &managedMemory) final {
    memoryManagerMutex_.lock();
    managedMemory->postProcess();
    if (managedMemory->canBeRecycled()) {
      managedMemory->clean();
      this->pool()->push_back(managedMemory);
    }
    memoryManagerMutex_.unlock();
  }

  /// Initialize the memory manager
  /// @brief Thread safe initialization, fill the pool with custom constructed object
  void initialize() final {
    memoryManagerMutex_.lock();
    if (!this->isInitialized()) {
      this->initialized();
      initialize(std::make_index_sequence<sizeof...(Args)>());
      this->initializeMemoryManager();
    }
    memoryManagerMutex_.unlock();
  }

  /// @brief Initialize implementation using the tuple of arguments stored
  /// @tparam Is Index of the arguments tuple
  template<size_t... Is>
  void initialize(std::index_sequence<Is...>) {
    std::for_each(
        this->pool()->begin(), this->pool()->end(),
        [this](std::shared_ptr<ManagedMemory> &emptyShared) {
          emptyShared = std::make_shared<T>(std::get<Is>(args_)...);
          emptyShared->memoryManager(this);
        }
    );
  }

  /// Getter to real managed type as string
  /// @return String of the real managed type
  [[nodiscard]] std::string managedType() const final { return hh::tool::typeToStr<T>(); }

};
}

#endif //HEDGEHOG_STATIC_MEMORY_MANAGER_H
</file11>

<file12>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_DOT_PRINTER_H
#define HEDGEHOG_DOT_PRINTER_H

#include <fstream>
#include <filesystem>
#include <iostream>
#include <cmath>
#include <utility>
#include <set>

#include "printer.h"
#include "options/color_scheme.h"
#include "options/color_picker.h"
#include "options/debug_options.h"
#include "options/structure_options.h"
#include "../../core/abstractions/base/node/graph_node_abstraction.h"
#include "../../core/abstractions/base/node/task_node_abstraction.h"
#include "../../core/abstractions/base/any_groupable_abstraction.h"
#include "options/input_option.h"
#include "../../core/abstractions/base/node/state_manager_node_abstraction.h"

/// @brief Hedgehog main namespace
namespace hh {

/// @brief Printer to produce a dot representation of the current state of the graph
/// @details https://www.graphviz.org/doc/info/lang.html
class DotPrinter : public Printer {
 private:
  /// @brief Representation of an edge for the Dot Printer
  class Edge {
   private:
    std::string id_{}; ///< Edge id

    std::string type_{}; ///< Edge type

    std::string extraLabel_{}; ///< Edge extra label (QS / MQS ...)

    std::set<std::string>
        arrivals_{}, ///< Arrival points (sender nodes) for the edge
    exits_{}; ///< Exit points (receiver nodes) for the edge

    bool declarationPrinted_ = false; ///< Flag, true if edge declaration printed

    core::abstraction::GraphNodeAbstraction *
        belongingGraph_ = nullptr; ///< Graph owning the edge

   public:
    /// @brief Edge constructor
    /// @param id Edge id
    /// @param type Edge type
    /// @param belongingGraph Graph owning the edge
    explicit Edge(std::string id, std::string type, core::abstraction::GraphNodeAbstraction *const belongingGraph)
        : id_(std::move(id)), type_(std::move(type)), belongingGraph_(belongingGraph) {}

    /// @brief Edge destructor
    virtual ~Edge() = default;

    /// @brief Edge id accessor
    /// @return Edge id
    [[nodiscard]] std::string const &id() const { return id_; }

    /// @brief Extra label accessor
    /// @return Extra label
    [[nodiscard]] std::string const &extraLabel() const { return extraLabel_; }

    /// @brief Belonging graph accessor
    /// @return Belonging graph
    [[nodiscard]] core::abstraction::GraphNodeAbstraction *belongingGraph() const { return belongingGraph_; }

    /// @brief Extra label setter
    /// @param extraLabel Extra label to set
    void addExtraLabel(std::string extraLabel) { extraLabel_ = std::move(extraLabel); }

    /// @brief Arrival point register
    /// @param arrival Arrival point to register
    void addArrival(std::string arrival) { arrivals_.insert(std::move(arrival)); }

    /// @brief Exit point register
    /// @param exit Exit point to register
    void addExit(std::string exit) { exits_.insert(std::move(exit)); }

    /// @brief Print declaration of an edge
    /// @param os Output stream used to print the edge declaration
    void printDeclaration(std::ostream &os) {
      if (!declarationPrinted_) {
        declarationPrinted_ = true;
        os << "\"" << id_ << "\"" << "[label=\"" << type_ << "\\n" << extraLabel_ << "\", shape=rect];\n";
      }
    }

    /// @brief Print all edges parts in the dot format
    /// @param os Output stream used to print all edges parts in the dot format
    void printEdges(std::ostream &os) const {
      for (auto &arrival : arrivals_) {
        os << "\"" << arrival << "\" -> \"" << id_ << "\"[penwidth=1, dir=none];\n";
      }
      for (auto &exit : exits_) {
        os << "\"" << id_ << "\" -> \"" << exit << "\"[penwidth=1];\n";
      }
    }

    /// @brief Equality operator
    /// @param rhs Edge to test against
    /// @return True if the two edges (this and rhs) are considered the same, else False
    bool operator==(Edge const &rhs) const { return id_ == rhs.id_ && type_ == rhs.type_; }
  };

  std::ofstream outputFile_ = {}; ///< Output file stream
  ColorScheme colorScheme_ = {}; ///< Color scheme chosen
  StructureOptions structureOptions_ = {}; ///< Structure options chosen
  InputOptions inputOptions_ = {}; ///< Input option chosen
  DebugOptions debugOptions_ = {}; ///< Debug option chosen
  std::unique_ptr<ColorPicker> colorPicker_ = nullptr; ///< Color picker used to generate the dot file

  std::chrono::nanoseconds
      graphTotalExecution_ = std::chrono::nanoseconds::max(), ///< Total graph execution
  minExecutionDurationInAllGraphs_ =
  std::chrono::nanoseconds::max(), ///< Minimum execution duration among all nodes in the graph
  maxExecutionDurationInAllGraphs_ =
  std::chrono::nanoseconds::min(), ///< Maximum execution duration among all nodes in the graph
  rangeExecutionDurationInAllGraphs_ =
  std::chrono::nanoseconds::min(),  ///< Execution duration range among all nodes in the graph
  minWaitDurationInAllGraphs_ =
  std::chrono::nanoseconds::max(),  ///< Minimum wait duration among all nodes in the graph
  maxWaitDurationInAllGraphs_ =
  std::chrono::nanoseconds::min(),  ///< Maximum wait duration among all nodes in the graph
  rangeWaitDurationInAllGraphs_ =
  std::chrono::nanoseconds::min();  ///< Execution wait range among all nodes in the graph

  std::unique_ptr<std::vector<Edge>> edges_ = nullptr; ///< All edges in the graph

 public:
  /// @brief DotPrinter constructor
  /// @param dotFilePath Path for the generated dot file
  /// @param colorScheme Color scheme options (Color depending on exec time or wait time)
  /// @param structureOptions Structure options
  /// @param inputOptions Input options
  /// @param debugOptions Debug options
  /// @param graph Graph to represent
  /// @param colorPicker Range of colors used to generate the dot file
  /// @param verbose Enable verbose mode: report when dot files are created or overwritten to standard out, default
  /// false.
  /// @throw std::runtime_error if the dot printer is not constructed with a valid ColorPicker
  DotPrinter(std::filesystem::path const &dotFilePath,
             ColorScheme colorScheme,
             StructureOptions structureOptions,
             InputOptions inputOptions,
             DebugOptions debugOptions,
             core::abstraction::GraphNodeAbstraction const *graph,
             std::unique_ptr<ColorPicker> colorPicker,
             bool verbose)
      : colorScheme_(colorScheme),
        structureOptions_(structureOptions),
        inputOptions_(inputOptions),
        debugOptions_(debugOptions),
        colorPicker_(std::move(colorPicker)),
        edges_(std::make_unique<std::vector<Edge>>()) {
    assert(graph != nullptr);

    testPath(dotFilePath, verbose);

    if (colorPicker_ == nullptr) {
      throw (
          std::runtime_error("A dot printer should be constructed with a valid ColorPicker (colorPicker != nullptr)")
      );
    }

    auto minMaxExecTime = graph->minMaxExecutionDuration();
    auto minMaxWaitTime = graph->minMaxWaitDuration();

    minExecutionDurationInAllGraphs_ = minMaxExecTime.first;
    maxExecutionDurationInAllGraphs_ = minMaxExecTime.second;

    minWaitDurationInAllGraphs_ = minMaxWaitTime.first;
    maxWaitDurationInAllGraphs_ = minMaxWaitTime.second;

    // Compute range
    rangeExecutionDurationInAllGraphs_ =
        maxExecutionDurationInAllGraphs_ == minExecutionDurationInAllGraphs_ ?
        std::chrono::nanoseconds(1) :
        maxExecutionDurationInAllGraphs_ - minExecutionDurationInAllGraphs_;

    rangeWaitDurationInAllGraphs_ =
        maxWaitDurationInAllGraphs_ == minWaitDurationInAllGraphs_ ?
        std::chrono::nanoseconds(1) :
        maxWaitDurationInAllGraphs_ - minWaitDurationInAllGraphs_;

    graphTotalExecution_ =
        graph->dequeueExecDuration() == std::chrono::nanoseconds::zero() ?
        std::chrono::system_clock::now() - graph->startExecutionTimeStamp() : graph->dequeueExecDuration();
  }

  /// @brief Dot Printer destructor
  ~DotPrinter() override { outputFile_.close(); }

  /// @brief Print graph header under dot format
  /// @param graph Graph to print
  void printGraphHeader(core::abstraction::GraphNodeAbstraction const *graph) override {
    // If the graph is the outer graph, i.e. the main graph
    if (!graph->isRegistered()) {
      outputFile_
          << "digraph " << graph->id()
          << " {\nlabel=\"" << graph->name();
      if (debugOptions_ == DebugOptions::ALL) { outputFile_ << " " << graph->id(); }

      outputFile_ << "\\nExecution duration:" << durationPrinter(this->graphTotalExecution_)
                  << "\\nCreation duration:" << durationPrinter(graph->graphConstructionDuration())
                  << "\"; fontsize=25; penwidth=5; labelloc=top; labeljust=left; \n";

      // If the graph is an inner graph, i.e. a graph of the outer graph
    } else {
      outputFile_ << "subgraph cluster" << graph->id() << " {\nlabel=\"" << graph->name();
      if (debugOptions_ == DebugOptions::ALL) {
        outputFile_ << " " << graph->id();
      }
      outputFile_
          << "\"; fontsize=25; penwidth=5; fillcolor=\""
          << colorFormatConvertor(graph->printOptions().background())
          << "\";\n";
    }
    outputFile_.flush();
  }

  /// @brief Print graph footer under dot format
  /// @param graph Graph to print
  void printGraphFooter(core::abstraction::GraphNodeAbstraction const *graph) override {

    // Print all edge declarations that has not already been printed
    for (auto &edge : *edges_) {
      if (edge.belongingGraph() == graph) {
        edge.printDeclaration(outputFile_);
      }
    }

    // If the graph is the outer graph
    if (!graph->isRegistered()) {
      // Print all the stored edges

      for (auto const &edge : *(this->edges_)) { edge.printEdges(outputFile_); }
    }
    // Close the dot subgraph
    outputFile_ << "}\n";
    outputFile_.flush();
  }

  /// @brief Print node information depending on the kind of node under the dot format
  /// @param node Node to print
  void printNodeInformation(core::abstraction::NodeAbstraction *node) override {
    // If the node is not a graph
    if (auto task = dynamic_cast<core::abstraction::TaskNodeAbstraction *>(node)) {
      //If all group node to be printed
      if (this->structureOptions_ == StructureOptions::ALL || this->structureOptions_ == StructureOptions::THREADING) {
        // Get and print the node information
        outputFile_ << getTaskInformation(task);
        // If only one node per group need to be printed with gathered information
      } else {
        if (auto copyableNode = dynamic_cast<core::abstraction::AnyGroupableAbstraction const *>(task)) {
          // If the node is the group main node
          if (copyableNode == copyableNode->groupRepresentative()) {
            // Get and print the node information
            outputFile_ << getTaskInformation(task);
          }
        } else {
          // Case for printing state manager while not printing all nodes
          outputFile_ << getTaskInformation(task);
        }
      }
    }
    outputFile_.flush();
  }

  /// @brief Print an edge between node from and to for the type edgetype under the dot format
  /// @param from Sender node
  /// @param to Receiving node
  /// @param edgeType Type of data transmitted through the edge
  /// @param queueSize Number of elements in the receiving queue
  /// @param maxQueueSize Maximum size of the receiving queue
  void printEdge(core::abstraction::NodeAbstraction const *from, core::abstraction::NodeAbstraction const *to,
                 std::string const &edgeType,
                 size_t const &queueSize, size_t const &maxQueueSize) override {

    std::ostringstream oss;
    std::string idToFind, label;

    for (auto &source : from->ids()) {
      for (auto &dest : to->ids()) {
        auto edge = getOrCreateEdge(dest.second, edgeType, to->belongingGraph());

        if (edge->extraLabel().empty()) {
          if (this->structureOptions_ == StructureOptions::QUEUE || this->structureOptions_ == StructureOptions::ALL) {
            oss << "QS=" << queueSize << "\\nMQS=" << maxQueueSize;
            edge->addExtraLabel(oss.str());
            oss.str("");
          }
        }
        edge->addArrival(source.first);
        edge->addExit(dest.first);

        if (this->structureOptions_ == StructureOptions::THREADING
            || this->structureOptions_ == StructureOptions::ALL) {
          if (auto copyableSender = dynamic_cast<core::abstraction::AnyGroupableAbstraction const *>(from)) {
            for (auto groupMember : *copyableSender->group()) { edge->addArrival(groupMember->nodeId()); }
          }
        }
      }
    }
  }

  /// @brief Print a group of nodes under the dot format
  /// @param representative Group node representative
  /// @param group Group of nodes
  /// @throw std::runtime_error if the group representative node does not derives from AnyGroupableAbstraction
  void printGroup(core::abstraction::NodeAbstraction *representative,
                  std::vector<core::abstraction::NodeAbstraction *> const &group) override {
    bool const printAllGroupMembers =
        this->structureOptions_ == StructureOptions::THREADING || this->structureOptions_ == StructureOptions::ALL;

    auto copyableRepr = dynamic_cast<core::abstraction::AnyGroupableAbstraction *>(representative);
    auto printRepr = dynamic_cast<core::abstraction::PrintableAbstraction *>(representative);
    if (copyableRepr == nullptr || printRepr == nullptr) {
      std::ostringstream oss;
      oss << "Internal error in: " << __FUNCTION__
          << " a group of node should be created with node that derives from AnyGroupableAbstraction and PrintableAbstraction";
      throw std::runtime_error(oss.str());
    }

    // Print header
    // If all group node to be printed
    if (printAllGroupMembers) {
      // Create a dot subgraph for the task group
      outputFile_ << "subgraph cluster" << representative->id()
                  << " {\nlabel=\"\"; penwidth=3; style=filled; fillcolor=\"#ebf0fa\"; color=\"#4e78cf\";\n";

    }

    printRepr->visit(this);

    if (printAllGroupMembers) {
      for (auto groupMember : group) {
        if (auto printGroupMember = dynamic_cast<core::abstraction::PrintableAbstraction *>(groupMember)) {
          printGroupMember->visit(this);
        } else {
          std::ostringstream oss;
          oss << "Internal error in: " << __FUNCTION__
              << " a group of node should be created with nodes that derive from AnyGroupableAbstraction and PrintableAbstraction";
          throw std::runtime_error(oss.str());
        }
      }
    }

    if (printAllGroupMembers) {
      outputFile_ << "}\n";
    }

    outputFile_.flush();
  }

  /// @brief Print outer graph source under the dot format
  /// @param source Source of the graph
  void printSource(core::abstraction::NodeAbstraction const *source) override {
    outputFile_ << source->id() << " [label=\"" << source->name();
    if (debugOptions_ == DebugOptions::ALL) {
      outputFile_ << " " << source->id() << " \\(Graph:" << source->belongingGraph()->id() << "\\)";
    }
    outputFile_ << "\", shape=invhouse];\n";
    outputFile_.flush();
  }

  /// @brief Print outer graph sink under the dot format
  /// @param sink Sink of the graph
  void printSink(core::abstraction::NodeAbstraction const *sink) override {
    outputFile_ << sink->id() << " [label=\"" << sink->name();
    if (debugOptions_ == DebugOptions::ALL) {
      outputFile_ << " " << sink->id() << " \\(Graph:" << sink->belongingGraph()->id() << "\\)";
    }
    outputFile_ << "\", shape=point];\n";
    outputFile_.flush();
  }

  /// @brief Print execution pipeline header under the dot format
  /// @param ep Execution pipeline to print
  /// @param switchNode Execution pipeline switch
  void printExecutionPipelineHeader(core::abstraction::ExecutionPipelineNodeAbstraction const *ep,
                                    core::abstraction::NodeAbstraction const *switchNode) override {
    //Print the dot subgraph header
    outputFile_ << "subgraph cluster" << ep->id() << " {\nlabel=\"" << ep->name();
    if (debugOptions_ == DebugOptions::ALL) { outputFile_ << " " << ep->id() << " / " << switchNode->id(); }
    // Print a "triangle" node to represent the execution pipeline switch
    outputFile_ << "\"; penwidth=1; style=dotted; style=filled; fillcolor=\""
                << colorFormatConvertor(ep->printOptions().background())
                << "\";\n "
                << switchNode->id() << "[label=\"\", shape=triangle];\n";
    outputFile_.flush();
  }

  /// @brief Print execution pipeline footer under the dot format
  void printExecutionPipelineFooter() override {
    outputFile_ << "}\n";
    outputFile_.flush();
  }

 private:
  /// @brief Get an existing edge or create a new edge
  /// @param id Edge id
  /// @param type Type transmitted through the edge
  /// @param belongingGraph Graph holding the edge
  /// @return Iterator to the edge
  std::vector<Edge>::iterator getOrCreateEdge(
      std::string const &id, std::string const &type,
      hh::core::abstraction::GraphNodeAbstraction *belongingGraph) {
    std::ostringstream ossId;
    ossId << "edge" << id << type;
    Edge temp(ossId.str(), type, belongingGraph);
    auto const &it = std::find(this->edges_->begin(), this->edges_->end(), temp);
    if (it != this->edges_->end()) { return it; }
    else { return this->edges_->insert(this->edges_->end(), temp); }
  }

  /// @brief Print under the dot format the information for a task
  /// @param task Task to print
  /// @return String containing all the information for a task under the dot format
  std::string getTaskInformation(core::abstraction::TaskNodeAbstraction *task) {
    std::stringstream ss;

    auto const copyableTask = dynamic_cast<core::abstraction::AnyGroupableAbstraction const *>(task);
    auto const slotTask = dynamic_cast<core::abstraction::SlotAbstraction *>(task);
    auto const sm = dynamic_cast<core::abstraction::StateManagerNodeAbstraction const *>(task);

    bool const printAllNodes =
        this->structureOptions_ == StructureOptions::THREADING || this->structureOptions_ == StructureOptions::ALL;

    // Print the name
    ss << task->id() << " [label=\"" << task->name();
    // Print the id (address) in case of debug
    if (debugOptions_ == DebugOptions::ALL) {
      ss << " " << task->id() << " \\(" << task->belongingGraph()->id() << "\\)";
    }

    // If the group has to be presented as a single dot node
    if (!printAllNodes) {
      if (copyableTask && copyableTask->isInGroup()) {
        ss << " x " << copyableTask->numberThreads();
      }
    }
    // If debug information printed
    if (debugOptions_ == DebugOptions::ALL) {
      if (slotTask) {
        // Print number of active input connection
        ss << "\\nActive inputs connection: " << slotTask->nbNotifierConnected();
      }
      // If all nodes in a group need to be printed
      if (printAllNodes) {
        ss << "\\nThread Active?: " << std::boolalpha << task->isActive();
        // If all nodes in a group should NOT be printed
      } else {
        if (copyableTask) {
          ss << "\\nActive threads: " << copyableTask->numberActiveThreadInGroup();
        }
      }
    }
    // If all nodes in a group need to be printed OR is state manager
    if (printAllNodes || sm) {
      if (inputOptions_ == InputOptions::GATHERED) {
        ss << "\\nElements: " << task->numberReceivedElements();
      } else {
        ss << "\\nElements/Input:";
        for (auto const &[typeStr, nbElements] : task->nbElementsPerInput()) {
          ss << " (" << typeStr << ")" << nbElements;
        }
      }

      ss << "\\nWait: " << durationPrinter(task->waitDuration());
      if (sm) {
        ss << "\\nLock state: " << durationPrinter(sm->acquireStateDuration());
        ss << "\\nEmpty ready list: " << durationPrinter(sm->emptyRdyListDuration());
      }

      if (inputOptions_ == InputOptions::GATHERED) {
        ss << "\\nDequeue+Exec: " << durationPrinter(task->dequeueExecDuration());
        ss << "\\nExec/Element: " << durationPrinter(task->averageExecutionDurationPerElement());
      } else {
        ss << "\\nDequeue+Exec/Input: ";
        for (auto const &[typeStr, duration] : task->dequeueExecutionDurationPerInput()) {
          ss << " (" << typeStr << ") " << durationPrinter(duration);
        }
        ss << "\\nExec/Element/Input:";
        for (auto const &[typeStr, duration] : task->averageExecutionDurationPerInputType()) {
          ss << " (" << typeStr << ") " << durationPrinter(duration);
        }
      }

      if (task->hasMemoryManagerAttached()) {
        ss << "\\nMemory manager (" << task->memoryManager()->managedType() << "): "
           << task->memoryManager()->currentSize() << "/" << task->memoryManager()->capacity();
        ss << "\\nMemory Wait: " << durationPrinter(task->memoryWaitDuration());
      }

      // If all nodes in a group should NOT be printed
    } else {
      //Get the time in the groups
      if (copyableTask) {
        // Print the number of element received per task

        if (copyableTask->numberThreads() > 1) {
          if (inputOptions_ == InputOptions::GATHERED) {
            ss << "\\nElements: ";
            auto minmaxElements = copyableTask->minmaxNumberElementsReceivedGroup();
            auto meanSDNumberElements = copyableTask->meanSDNumberElementsReceivedGroup();
            ss << "Min: " << minmaxElements.first << ""
               << " / Avg: " << std::setw(1) << meanSDNumberElements.first
               << " +- " << std::setw(1) << meanSDNumberElements.second
               << " / Max: " << minmaxElements.second;
          } else {
            ss << "\\nElements/Input: ";
            auto minmaxElementsPerInputs = copyableTask->minmaxNumberElementsReceivedGroupPerInput();
            auto meanSDNumberElementsPerInputs = copyableTask->meanSDNumberElementsReceivedGroupPerInput();
            for (const auto &[key, minMax] : minmaxElementsPerInputs) {
              ss << "\\n(" << key << ") Min: " << minMax.first
                 << " Avg: " << std::setw(1) << meanSDNumberElementsPerInputs.at(key).first
                 << " +- " << std::setw(1) << meanSDNumberElementsPerInputs.at(key).second
                 << " Max: " << minMax.second;
            }
          }
        } else {
          if (inputOptions_ == InputOptions::GATHERED) {
            ss << "\\nElements: ";
            ss << task->numberReceivedElements();
          } else {
            ss << "\\nElements/Input:";
            for (const auto &[key, nbElem] : task->nbElementsPerInput()) {
              ss << " (" << key << ") " << nbElem;
            }
          }
        }
        // Print the wait time
        ss << "\nWait Time: ";
        if (copyableTask->numberThreads() > 1) {
          auto minmaxWait = copyableTask->minmaxWaitDurationGroup();
          auto meanSDWait = copyableTask->meanSDWaitDurationGroup();
          ss << "Min: " << durationPrinter(minmaxWait.first)
             << " / Avg: " << durationPrinter(meanSDWait.first)
             << " +- " << durationPrinter(meanSDWait.second)
             << " / Max: " << durationPrinter(minmaxWait.second) << "\\n";
        } else { ss << durationPrinter(task->waitDuration()) << "\\n"; }
        // Print the execution time
        if (inputOptions_ == InputOptions::GATHERED) {
          ss << "Dequeue+Exec: ";
          if (copyableTask->numberThreads() > 1) {
            auto minmaxExec = copyableTask->minmaxDequeueExecutionDurationGroup();
            auto meanSDExec = copyableTask->meanSDDequeueExecutionDurationGroup();
            ss << "Min: " << durationPrinter(minmaxExec.first)
               << " / Avg: " << durationPrinter(meanSDExec.first)
               << " +- " << durationPrinter(meanSDExec.second)
               << " / Max: " << durationPrinter(minmaxExec.second) << "\\n";
          } else { ss << durationPrinter(task->dequeueExecDuration()) << "\\n"; }
        } else {
          ss << "Dequeue+Exec/Input:";
          if (copyableTask->numberThreads() > 1) {
            auto minmaxExec = copyableTask->minmaxDequeueExecutionDurationGroupPerInput();
            auto meanSDExec = copyableTask->meanSDDequeueExecutionDurationGroupPerInput();
            for (auto const &[key, minMax] : minmaxExec) {
              ss << "\\n(" << key << ") Min: " << durationPrinter(minmaxExec.at(key).first)
                 << " / Avg: " << durationPrinter(meanSDExec.at(key).first)
                 << " +- " << durationPrinter(meanSDExec.at(key).second)
                 << " / Max: " << durationPrinter(minmaxExec.at(key).second);
            }
            ss << "\\n";
          } else {
            for (auto const &[key, duration] : task->dequeueExecutionDurationPerInput()) {
              ss << " (" << key << ") " << durationPrinter(duration);
            }
            ss << "\\n";
          }

        }
        // Print the execution time per Element
        if (inputOptions_ == InputOptions::GATHERED) {
          ss << "Exec: ";
          if (copyableTask->numberThreads() > 1) {
            auto minmaxExecPerElement = copyableTask->minmaxExecTimePerElementGroup();
            auto meanSDExecPerElement = copyableTask->meanSDExecTimePerElementGroup();
            ss
                << "  Min: " << durationPrinter(minmaxExecPerElement.first)
                << " / Avg: " << durationPrinter(meanSDExecPerElement.first) << " +- "
                << durationPrinter(meanSDExecPerElement.second)
                << " / Max: " << durationPrinter(minmaxExecPerElement.second) << "\\n";
          } else { ss << durationPrinter(task->averageExecutionDurationPerElement()) << "\\n"; }
        } else {
          ss << "Exec/input: ";
          if (copyableTask->numberThreads() > 1) {
            auto minMaxExec = copyableTask->minmaxExecTimePerElementGroupPerInput();
            auto meanSDExec = copyableTask->meanSDExecTimePerElementGroupPerInput();
            for (auto const &[key, minMax] : minMaxExec) {
              ss << "\\n(" << key << ") Min: " << durationPrinter(minMaxExec.at(key).first)
                 << " / Avg: " << durationPrinter(meanSDExec.at(key).first)
                 << " +- " << durationPrinter(meanSDExec.at(key).second)
                 << " / Max: " << durationPrinter(minMaxExec.at(key).second);
            }
            ss << "\\n";
          } else {
            for (auto const &[key, duration] : task->executionDurationPerInput()) {
              ss << " (" << key << ") " << durationPrinter(duration);
            }
            ss << "\\n";
          }
        }

        // Print the memory wait time
        if (task->hasMemoryManagerAttached()) {
          ss << "Memory manager (" << task->memoryManager()->managedType() << "): "
             << task->memoryManager()->currentSize() << "/" << task->memoryManager()->capacity();
          ss << "\\nMemory Wait Time: ";
          if (copyableTask->numberThreads() == 1) {
            ss << durationPrinter(task->memoryWaitDuration()) << "\\n";
          } else {
            auto minmaxWaitMemory = copyableTask->minmaxMemoryWaitTimeGroup();
            auto meanSDWaitMemory = copyableTask->meanSDMemoryWaitTimePerElementGroup();
            ss
                << "  Min: " << durationPrinter(minmaxWaitMemory.first) << "\\n"
                << "  Avg: " << durationPrinter(meanSDWaitMemory.first) << " +-"
                << durationPrinter(meanSDWaitMemory.second) << "\\n"
                << "  Max: " << durationPrinter(minmaxWaitMemory.second) << "\\n";
          }
        }
      }
    }
    // If extra information has been defined by the user, print it
    auto extraInfo = task->extraPrintingInformation();
    if (!extraInfo.empty()) { ss << "\\n" << extraInfo; }

    ss << "\"";
    ss << ",shape=rect";
    // Change the color of the rect depending on the user choice
    switch (this->colorScheme_) {
      case ColorScheme::EXECUTION:ss << ",color=" << this->getExecRGB(task->dequeueExecDuration()) << ", penwidth=3";
        break;
      case ColorScheme::WAIT:ss << ",color=" << this->getWaitRGB(task->waitDuration()) << ", penwidth=3";
        break;
      default:break;
    }

    ss << R"(, style=filled, fillcolor=")"
       << colorFormatConvertor(task->printOptions().background())
       << R"(", fontcolor=")"
       << colorFormatConvertor(task->printOptions().font())
       << "\"];\n";
    return ss.str();
  }

  /// @brief Test the path given by the user, print extra information if verbose is used
  /// @param dotFilePath Path to test
  /// @param verbose Verbose option
  /// @throw std::runtime_error if the dotFilePath is not valid (do not represent a file and parent path does not exist)
  void testPath(std::filesystem::path const &dotFilePath, bool verbose) {
    auto directoryPath = dotFilePath.parent_path();
    std::ostringstream oss;
    if (!dotFilePath.has_filename()) {
      oss << "The path: " << dotFilePath << " does not represent a file.";
      throw (std::runtime_error(oss.str()));
    }
    if (!std::filesystem::exists(directoryPath)) {
      oss << "The file " << dotFilePath.filename() << " can not be store in " << directoryPath
          << " because the directory does not  exist.";
      throw (std::runtime_error(oss.str()));
    }
    if (!std::filesystem::exists(directoryPath)) {
      oss << "The file " << dotFilePath.filename() << " can not be store in " << directoryPath
          << " because the directory does not  exist.";
      throw (std::runtime_error(oss.str()));
    }
    if (verbose) {
      if (std::filesystem::exists(dotFilePath)) {
        std::cout << "The file " << dotFilePath.filename() << " will be overwritten." << std::endl;
      } else {
        std::cout << "The file " << dotFilePath.filename() << " will be created." << std::endl;
      }
    }
    outputFile_ = std::ofstream(dotFilePath);
  }

  /// @brief Get the rgb color for the execution time value
  /// @param ns Execution value to get the RGB color
  /// @return RGB color for val
  std::string getExecRGB(std::chrono::nanoseconds const &ns) {
    return colorPicker_
        ->getRGBFromRange(ns, this->minExecutionDurationInAllGraphs_, this->rangeExecutionDurationInAllGraphs_);
  }

  /// @brief Get the rgb color for the wait time value
  /// @param ns Execution value to get the RGB color
  /// @return RGB color for val
  std::string getWaitRGB(std::chrono::nanoseconds const &ns) {
    return colorPicker_->getRGBFromRange(ns, this->minWaitDurationInAllGraphs_, this->rangeWaitDurationInAllGraphs_);
  }

  /// @brief Print a duration with the right precision
  /// @param ns duration in ns
  /// @return String representing a duration with the right format
  static std::string durationPrinter(std::chrono::nanoseconds const &ns) {
    std::ostringstream oss;

    // Cast with precision loss
    auto s = std::chrono::duration_cast<std::chrono::seconds>(ns);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(ns);
    auto us = std::chrono::duration_cast<std::chrono::microseconds>(ns);

    if (s > std::chrono::seconds::zero()) {
      oss << s.count() << "." << std::setfill('0') << std::setw(3) << (ms - s).count() << "s";
    } else if (ms > std::chrono::milliseconds::zero()) {
      oss << ms.count() << "." << std::setfill('0') << std::setw(3) << (us - ms).count() << "ms";
    } else if (us > std::chrono::microseconds::zero()) {
      oss << us.count() << "." << std::setfill('0') << std::setw(3) << (ns - us).count() << "us";
    } else {
      oss << ns.count() << "ns";
    }
    return oss.str();
  }

  /// @brief Print a color into a format understood by Graphiz
  /// @param color Color definition
  /// @return String containing the color representation
  static std::string colorFormatConvertor(hh::tool::PrintOptions::Color const &color) {
    std::ostringstream ss;
    ss << "#"
       << std::setw(2) << std::setfill('0') << std::hex << (int) color.r_
       << std::setw(2) << std::setfill('0') << std::hex << (int) color.g_
       << std::setw(2) << std::setfill('0') << std::hex << (int) color.b_
       << std::setw(2) << std::setfill('0') << std::hex << (int) color.a_;

    return ss.str();
  }
};

}

#endif //HEDGEHOG_DOT_PRINTER_H
</file12>

<file13>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_HEDGEHOG_EXPORT_FILE_H_
#define HEDGEHOG_HEDGEHOG_EXPORT_FILE_H_

#include <map>
#include <list>
#include <vector>
#include <fstream>
#include <unordered_set>

#include "printer.h"
#include "../../core/abstractions/base/node/graph_node_abstraction.h"
#include "../../core/abstractions/base/node/task_node_abstraction.h"
#include "../../core/abstractions/base/any_groupable_abstraction.h"

/// @brief Hedgehog main namespace
namespace hh {

/// @brief Printer to produce a representation of the the graph structure in a json format for the GUI
class HedgehogExportFile : public Printer {
 private:
  std::ofstream outputFile_ = {}; ///< Output file stream
  std::ostringstream buffer_; ///< Buffer for the file

  std::map<std::pair<core::abstraction::NodeAbstraction const *, core::abstraction::NodeAbstraction const *>,
           std::list<std::string>> edges_; ///< list of edges to print
  std::map<core::abstraction::NodeAbstraction const *, std::pair<std::string, size_t>> mapExecutionPipelineAlias_; ///< Mapping of execution pipeline node and its switch to an alias name
 public:
  /// @brief Create a HedgehogExportFile from the graph pointer
  /// @details the graph's name is the name of the file + ".hhrojson"
  /// @param graph Pointer to the graph
  explicit HedgehogExportFile(core::abstraction::GraphNodeAbstraction const *graph) {
    outputFile_.open(graph->name() + ".hhrojson");
  }

  /// @brief Put the buffer content in the file and close the file
  ~HedgehogExportFile() override {
    outputFile_ << buffer_.str();
    outputFile_.close();
  }

  /// @brief Print graph header under json format
  /// @param graph Graph to print
  void printGraphHeader(core::abstraction::GraphNodeAbstraction const *graph) override {
    buffer_ << "{\n";
    // If the graph is the outer graph, i.e. the main graph
    if (!graph->isRegistered()) {
      buffer_ << "\"type\": \"graph\",\n";
    } else {
      buffer_ << "\"type\": \"innerGraph\",\n";
      buffer_ << R"("graphIdentifier": ")" << graph->graphId() << "\",\n";
    }
    buffer_ << R"("instanceIdentifier": ")" << graph->name() << "\",\n";
    // Open the node definitions
    buffer_ << R"("nodes": [)" << "\n";
  }

  /// @brief Print graph footer under json format
  /// @param graph Graph to print
  void printGraphFooter(core::abstraction::GraphNodeAbstraction const *graph) override {
    std::pair<std::string, size_t> infoSrc, infoDest;
    // Remove ",\n"
    buffer_.seekp(-2, buffer_.cur);
    // Close the node definitions
    buffer_ << "\n],\n";
    // If the graph is the outer graph, i.e. the main graph
    if (!graph->isRegistered()) {
      // Export edges
      buffer_ << "\"edges\": [\n";
      for (auto const &edge : edges_) {
        auto const &[src, dest] = edge.first;

        if(mapExecutionPipelineAlias_.contains(src)){ infoSrc = mapExecutionPipelineAlias_.at(src);}
        else { infoSrc = {src->name(), src->graphId()}; }

        if(mapExecutionPipelineAlias_.contains(dest)){ infoDest = mapExecutionPipelineAlias_.at(dest);}
        else { infoDest = {dest->name(), dest->graphId()}; }

        buffer_ << "{\n";
        buffer_
            << R"("sourceId": ")" << infoSrc.first << "\",\n"
            << R"("sourceGraphId": ")" << infoSrc.second << "\",\n"
            << R"("destId": ")" << infoDest.first << "\",\n"
            << R"("destGraphId": ")" << infoDest.second << "\",\n"
            << R"("types": [)" << "\n";
        auto const &types = edge.second;
        for (auto const &type : types) {
          buffer_ << "\"" << type << "\",\n";
        }
        // Remove ",\n"
        buffer_.seekp(-2, buffer_.cur);
        buffer_ << "\n]\n},\n";
      } // for all edges
      // Remove ",\n"
      buffer_.seekp(-2, buffer_.cur);
      buffer_ << "\n]\n}";
    } else { // Not main graph
      // Remove ",\n"
      buffer_.seekp(-2, buffer_.cur);
      buffer_ << "},\n";
    }// if else main graph
  }

  /// @brief Print execution pipeline header under the json format
  /// @param ep Execution pipeline to print
  /// @param switchNode Execution pipeline switch
  void printExecutionPipelineHeader(core::abstraction::ExecutionPipelineNodeAbstraction const *ep,
                                    [[maybe_unused]] core::abstraction::NodeAbstraction const *switchNode) override {
    buffer_ << "{\n";
    buffer_ << "\"type\": \"executionPipeline\",\n";
    buffer_ << R"("instanceIdentifier": ")" << ep->name() << "\",\n";
    buffer_ << R"("graphIdentifier": ")" << switchNode->graphId() << "\",\n";
    buffer_ << R"("switch": ")" << switchNode->name() << "\",\n";
    buffer_ << "\"graphs\": [";

    std::ostringstream oss;
    oss << ep->name() << " switch";

    mapExecutionPipelineAlias_.insert({ep, {oss.str(), switchNode->graphId()}});
    mapExecutionPipelineAlias_.insert({switchNode, {oss.str(), switchNode->graphId()}});
  }

  /// @brief Print execution pipeline footer under the json format
  void printExecutionPipelineFooter() override {
    // Remove ",\n"
    buffer_.seekp(-2, buffer_.cur);
    buffer_ << "\n]\n},";
  }

  /// @brief Print node information depending on the kind of node under the json format
  /// @param node Node to print
  void printNodeInformation(core::abstraction::NodeAbstraction *node) override {
    auto const &nodeAsTask = dynamic_cast<core::abstraction::TaskNodeAbstraction *>(node);
    auto const &nodeAsSM = dynamic_cast<core::abstraction::StateManagerNodeAbstraction const *>(node);
    auto copyableNode = dynamic_cast<core::abstraction::AnyGroupableAbstraction const *>(node);
    buffer_ << "{\n";
    if (nodeAsSM) {
      buffer_ << "\"type\": \"stateManager\",\n";
    } else if (nodeAsTask) {
      buffer_ << "\"type\": \"task\",\n";
    } else {
      buffer_ << "\"type\": \"other\",\n";
    }
    buffer_ << R"("instanceIdentifier": ")" << node->name() << "\",\n";
    buffer_ << R"("graphIdentifier": ")" << node->graphId() << "\",\n";
    if (nodeAsTask && nodeAsTask->hasMemoryManagerAttached()) {
      buffer_ << R"("managedMemory": ")" << nodeAsTask->memoryManager()->managedType() << "\",\n";
    }
    if (copyableNode) { buffer_ << R"("thread": )" << copyableNode->numberThreads() << "\n"; }
    else { buffer_ << R"("thread": 1)" << "\n"; }
    buffer_ << "},\n";
  }

  /// @brief Print an edge between node from and to for the type edgetype under the json format
  /// @param from Sender node
  /// @param to Receiving node
  /// @param edgeType Type of data transmitted through the edge
  /// @param queueSize Number of elements in the receiving queue [unused]
  /// @param maxQueueSize Maximum size of the receiving queue [unused]
  void printEdge(core::abstraction::NodeAbstraction const *from,
                 core::abstraction::NodeAbstraction const *to,
                 std::string const &edgeType,
                 [[maybe_unused]]size_t const &queueSize,
                 [[maybe_unused]]size_t const &maxQueueSize) override {
    std::pair<core::abstraction::NodeAbstraction const *, core::abstraction::NodeAbstraction const *> key{from, to};
    if (!edges_.contains(key)) { edges_.insert({key, {}}); }
    edges_[key].push_back(edgeType);
  }

  /// @brief Print a group of nodes under the json format
  /// @param representative Group node representative (only one actually printed)
  /// @param group Group of nodes [unused]
  /// @throw std::runtime_error if the group representative node does not derives from AnyGroupableAbstraction
  void printGroup(core::abstraction::NodeAbstraction *representative,
                  [[maybe_unused]]std::vector<core::abstraction::NodeAbstraction *> const &group) override {
    auto printRepr = dynamic_cast<core::abstraction::PrintableAbstraction *>(representative);
    if (printRepr == nullptr) {
      std::ostringstream oss;
      oss << "Internal error in: " << __FUNCTION__
          << " a group of node should be created with node that derives from AnyGroupableAbstraction and PrintableAbstraction";
      throw std::runtime_error(oss.str());
    }
    printRepr->visit(this);
  }

  /// @brief Do nothing, the source already exists by default in the GUI
  /// @param source Source to print (unused)
  void printSource([[maybe_unused]]core::abstraction::NodeAbstraction const *source) override {
    buffer_ << "{\n";
    buffer_ << "\"type\": \"IONode\",\n";
    buffer_ << R"("instanceIdentifier": ")" << source->name() << "\",\n";
    buffer_ << R"("graphIdentifier": ")" << source->graphId() << "\",\n";
    buffer_ << R"("thread": 1)" << "\n";
    buffer_ << "},\n";
  }
  /// @brief Do nothing, the sink already exists by default in the GUI
  /// @param sink Sink to print (unused)
  void printSink([[maybe_unused]]core::abstraction::NodeAbstraction const *sink) override {
    buffer_ << "{\n";
    buffer_ << "\"type\": \"IONode\",\n";
    buffer_ << R"("instanceIdentifier": ")" << sink->name() << "\",\n";
    buffer_ << R"("graphIdentifier": ")" << sink->graphId() << "\",\n";
    buffer_ << R"("thread": 1)" << "\n";
    buffer_ << "},\n";
  }
};
}
#endif //HEDGEHOG_HEDGEHOG_EXPORT_FILE_H_
</file13>

<file14>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_PRINTER_H
#define HEDGEHOG_PRINTER_H

#include <set>
#include <memory>
#include <ostream>

/// @brief Hedgehog main namespace
namespace hh {

/// @brief Hedgehog core namespace
namespace core {
/// @brief Hedgehog abstraction namespace
namespace abstraction {

#ifndef DOXYGEN_SHOULD_SKIP_THIS

/// @brief Forward declaration NodeAbstraction
class NodeAbstraction;
/// @brief Forward declaration GraphNodeAbstraction
class GraphNodeAbstraction;
/// @brief Forward declaration AnyGroupableAbstraction
class AnyGroupableAbstraction;
/// @brief Forward declaration ExecutionPipelineNodeAbstraction
class ExecutionPipelineNodeAbstraction;
#endif //DOXYGEN_SHOULD_SKIP_THIS

}
}

/// @brief Printer abstraction to get a snapshot of the metrics of the Hedgehog graph
class Printer {
 private:
  std::unique_ptr<std::set<core::abstraction::NodeAbstraction const * >>
      uniqueNodes_ = nullptr; ///< Uniques Nodes registered (already printed)

 public:
  /// @brief Default constructor
  Printer() : uniqueNodes_(std::make_unique<std::set<core::abstraction::NodeAbstraction const * >>()) {}

  /// @brief Default destructor
  virtual ~Printer() = default;

  /// @brief Print graph header
  /// @param graph Graph to print
  virtual void printGraphHeader(core::abstraction::GraphNodeAbstraction const *graph) = 0;

  /// @brief Print graph footer
  /// @param graph Graph to print
  virtual void printGraphFooter(core::abstraction::GraphNodeAbstraction const *graph) = 0;

  /// @brief Print execution pipeline header
  /// @param ep Execution pipeline to print
  /// @param switchNode Execution pipeline switch
  virtual void printExecutionPipelineHeader(
      core::abstraction::ExecutionPipelineNodeAbstraction const *ep,
      core::abstraction::NodeAbstraction const *switchNode) = 0;

  /// @brief Print execution pipeline footer
  virtual void printExecutionPipelineFooter() = 0;

  /// @brief Print node information
  /// @param node Node to print
  virtual void printNodeInformation(core::abstraction::NodeAbstraction *node) = 0;

  /// @brief Print edge information
  /// @param from From node
  /// @param to To node
  /// @param edgeType Type linked to the edge
  /// @param queueSize Queue current numverElementsReceived
  /// @param maxQueueSize Queue maximum numverElementsReceived
  virtual void printEdge(core::abstraction::NodeAbstraction const *from, core::abstraction::NodeAbstraction const *to,
                         std::string const &edgeType,
                         size_t const &queueSize, size_t const &maxQueueSize) = 0;

  /// @brief Print group of nodes
  /// @param representative Group's representative
  /// @param group Group of nodes
  virtual void printGroup(core::abstraction::NodeAbstraction *representative,
                          std::vector<core::abstraction::NodeAbstraction *> const &group) = 0;

  /// @brief Print outer graph source
  /// @param source Graph source
  virtual void printSource(core::abstraction::NodeAbstraction const *source) = 0;

  /// @brief Print outer graph sink
  /// @param sink Graph sink
  virtual void printSink(core::abstraction::NodeAbstraction const *sink) = 0;

  /// @brief Register a visited node
  /// @param nodeAbstraction Node to register
  /// @return True if registered, false if already registered
  bool registerNode(core::abstraction::NodeAbstraction const *nodeAbstraction) {
    return uniqueNodes_->insert(nodeAbstraction).second;
  }
};

}

#endif //HEDGEHOG_PRINTER_H
</file14>

<file15>

// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_BLUE_TO_RED_COLOR_H
#define HEDGEHOG_BLUE_TO_RED_COLOR_H

#include <cmath>
#include <sstream>
#include <iomanip>
#include <algorithm>

#include "../options/color_picker.h"

/// @brief Hedgehog main namespace
namespace hh {

/// Blue to Red color range.
/// @brief Return a color from only blue to only red, blue being the lowest value, red the highest value in range
class BlueToRedColor : public ColorPicker {
 public:
  /// @brief Default constructor
  BlueToRedColor() = default;
  /// @brief Default destructor
  ~BlueToRedColor() override = default;

  /// @brief Return a color from only blue to only red, blue being the lowest value, red the highest value in range
  /// @param value Value to get the color from
  /// @param min Minimum value of the range
  /// @param range Range of values
  /// @return RGB color for the  value
  std::string getRGBFromRange(std::chrono::nanoseconds const &value,
                              std::chrono::nanoseconds const &min,
                              std::chrono::nanoseconds const &range) override {

    auto posRedToBlue = (uint64_t) std::round((double) (value.count() - min.count()) / (double) range.count() * 255);
    posRedToBlue = std::clamp(posRedToBlue, (uint64_t) 0, (uint64_t) 255);
    std::stringstream ss;
    ss << "\"#"
       << std::setfill('0') << std::setw(2) << std::hex << posRedToBlue
       << "00"
       << std::setfill('0') << std::setw(2) << std::hex << 255 - posRedToBlue
       << "\"";

    return ss.str();
  }

};

}

#endif //HEDGEHOG_BLUE_TO_RED_COLOR_H
</file15>

<file16>

// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_JET_COLOR_H
#define HEDGEHOG_JET_COLOR_H

#include <sstream>
#include <iomanip>

#include "../options/color_picker.h"

/// @brief Hedgehog main namespace
namespace hh {

/// Jet color range.
/// @brief Return a color from the jet color range
class JetColor : public ColorPicker {
 public:
  /// @brief Default constructor
  JetColor() = default;

  /// @brief Default destructor
  ~JetColor() override = default;

  /// @brief Get RGB value for a duration within a range for the jet color range
  /// @param value Value to get the RGB color
  /// @param min Min value in the range
  /// @param range Range of values
  /// @return String representing the RGB values
  std::string getRGBFromRange(std::chrono::nanoseconds const &value,
                              std::chrono::nanoseconds const &min,
                              std::chrono::nanoseconds const &range) override {
    double
        dVal = (double) value.count(), dMin = (double) min.count(), dRange = (double) range.count(),
        dR = 1, dG = 1, dB = 1;

    std::ostringstream oss;

    if (dVal < dMin + 0.25 * dRange) {
      dR = 0;
      dG = (4 * dVal - dMin) / dRange;
    } else if (dVal < (dMin + 0.5 * dRange)) {
      dR = 0;
      dB = 1 + 4 * (dMin + 0.25 * dRange - dVal) / dRange;
    } else if (dVal < (dMin + 0.75 * dRange)) {
      dR = 4 * (dVal - dMin - 0.5 * dRange) / dRange;
      dB = 0;
    } else {
      dG = 1 + 4 * (dMin + 0.75 * dRange - dVal) / dRange;
      dB = 0;
    }

    oss << "\"#"
        << std::setfill('0') << std::setw(2) << std::hex << (uint16_t) std::clamp(dR * 255, 0., 255.)
        << std::setfill('0') << std::setw(2) << std::hex << (uint16_t) std::clamp(dG * 255, 0., 255.)
        << std::setfill('0') << std::setw(2) << std::hex << (uint16_t) std::clamp(dB * 255, 0., 255.)
        << "\"";

    return oss.str();
  }
};

}

#endif //HEDGEHOG_JET_COLOR_H
</file16>

<file17>

// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_COLOR_PICKER_H
#define HEDGEHOG_COLOR_PICKER_H

#include <string>
#include <chrono>

/// @brief Hedgehog main namespace
namespace hh {

/// @brief Color scheme abstraction for dot file generation
class ColorPicker {
 public:
  /// @brief Default constructor
  ColorPicker() = default;
  /// @brief Default destructor
  virtual ~ColorPicker() = default;

  /// @brief Create a RGB value in the form of a string from a value and its range
  /// @param value Time in nanoseconds to represent in RGB
  /// @param min Min range value (in nanoseconds)
  /// @param range Range of values (in nanoseconds)
  /// @return RGB value in the form of a string from a value and its range
  virtual std::string getRGBFromRange(
      std::chrono::nanoseconds const &value,
      std::chrono::nanoseconds const &min, std::chrono::nanoseconds const &range) = 0;
};
}

#endif //HEDGEHOG_COLOR_PICKER_H
</file17>

<file18>
//  NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
//  software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
//  derivative works of the software or any portion of the software, and you may copy and distribute such modifications
//  or works. Modified works should carry a notice stating that you changed the software and should note the date and
//  nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
//  source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
//  EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
//  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
//  WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
//  CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
//  THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
//  are solely responsible for determining the appropriateness of using and distributing the software and you assume
//  all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
//  with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
//  operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
//  damage to property. The software developed by NIST employees is not subject to copyright protection within the
//  United States.

#ifndef HEDGEHOG_COLOR_SCHEME_H
#define HEDGEHOG_COLOR_SCHEME_H

/// @brief Hedgehog main namespace
namespace hh {
/// @brief Enum color options
enum class ColorScheme {
  NONE, ///< No added coloration
  EXECUTION, ///< Colors nodes based on execution time
  WAIT ///< Colors nodes based on wait time
};
}

#endif //HEDGEHOG_COLOR_SCHEME_H
</file18>

<file19>
//  NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
//  software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
//  derivative works of the software or any portion of the software, and you may copy and distribute such modifications
//  or works. Modified works should carry a notice stating that you changed the software and should note the date and
//  nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
//  source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
//  EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
//  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
//  WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
//  CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
//  THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
//  are solely responsible for determining the appropriateness of using and distributing the software and you assume
//  all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
//  with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
//  operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
//  damage to property. The software developed by NIST employees is not subject to copyright protection within the
//  United States.

#ifndef HEDGEHOG_DEBUG_OPTIONS_H
#define HEDGEHOG_DEBUG_OPTIONS_H

/// @brief Hedgehog main namespace
namespace hh {
/// @brief Enum to enable debug printing
enum class DebugOptions {
  NONE, ///< No added debug options
  ALL ///< Shows debug information such as pointer addresses for nodes and edges
};
}

#endif //HEDGEHOG_DEBUG_OPTIONS_H
</file19>

<file20>
//  NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
//  software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
//  derivative works of the software or any portion of the software, and you may copy and distribute such modifications
//  or works. Modified works should carry a notice stating that you changed the software and should note the date and
//  nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
//  source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
//  EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
//  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
//  WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
//  CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
//  THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
//  are solely responsible for determining the appropriateness of using and distributing the software and you assume
//  all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
//  with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
//  operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
//  damage to property. The software developed by NIST employees is not subject to copyright protection within the
//  United States.

#ifndef HEDGEHOG_INPUT_OPTION_H
#define HEDGEHOG_INPUT_OPTION_H

/// @brief Hedgehog main namespace
namespace hh {
/// @brief Enum to choose the execution time format depending on the input types
enum class InputOptions {
  GATHERED, ///< Present the time for all input type gathered
  SEPARATED ///< Shows the time per input type
};
}

#endif //HEDGEHOG_INPUT_OPTION_H
</file20>

<file21>
//  NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
//  software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
//  derivative works of the software or any portion of the software, and you may copy and distribute such modifications
//  or works. Modified works should carry a notice stating that you changed the software and should note the date and
//  nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
//  source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
//  EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
//  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
//  WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
//  CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
//  THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
//  are solely responsible for determining the appropriateness of using and distributing the software and you assume
//  all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
//  with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
//  operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
//  damage to property. The software developed by NIST employees is not subject to copyright protection within the
//  United States.

#ifndef HEDGEHOG_STRUCTURE_OPTIONS_H
#define HEDGEHOG_STRUCTURE_OPTIONS_H

/// @brief Hedgehog main namespace
namespace hh {
/// @brief Enum structural options
enum class StructureOptions {
  NONE, ///< No added structural options
  THREADING, ///< Displays all tasks in a thread group
  QUEUE, ///< Displays queue details (max queue numberElementsReceived and queue numberElementsReceived along edges)
  ALL ///< Displays both THREADING and QUEUE
};
}

#endif //HEDGEHOG_STRUCTURE_OPTIONS_H
</file21>

<file22>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_ABSTRACT_STATE_H
#define HEDGEHOG_ABSTRACT_STATE_H

#include <shared_mutex>

#include "../../tools/traits.h"
#include "../../behavior/cleanable.h"
#include "../../behavior/multi_execute.h"
#include "../../behavior/input_output/state_multi_senders.h"
#include "../../core/nodes/core_state_manager.h"

#include "../memory_manager/manager/abstract_memory_manager.h"

/// @brief Hedgehog main namespace
namespace hh {

/// Hedgehog AbstractState
/// @brief The state holds the data structures that are used to manage the flow of data and organize
/// rendez-vous points or other synchronization mechanisms. It is managed and used through a StateManager, and is thread safe.
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
class AbstractState
    : public behavior::Cleanable,
      public tool::BehaviorMultiExecuteTypeDeducer_t<tool::Inputs<Separator, AllTypes...>>,
      public tool::BehaviorStateMultiSendersTypeDeducer_t<tool::Outputs<Separator, AllTypes...>> {
#ifndef DOXYGEN_SHOULD_SKIP_THIS
  /// @brief Declare core::CoreStateManager as friend
  friend core::CoreStateManager<Separator, AllTypes...>;
#endif //DOXYGEN_SHOULD_SKIP_THIS
 private:
  mutable std::unique_ptr<std::shared_mutex> mutex_ = nullptr; ///< Mutex to protect the state
  StateManager<Separator, AllTypes...> *stateManager_ = nullptr; ///< AbstractState manager currently using the state
 public:
  /// @brief Default state constructor
  AbstractState() : mutex_(std::make_unique<std::shared_mutex>()) {}
  /// @brief Default state destructor
  ~AbstractState() override = default;

  /// @brief Accessor to the managed memory if a memory manager has been attached to a StateManager
  /// @return Return a managed memory from the memory manager attached to the state manager
  std::shared_ptr<ManagedMemory> getManagedMemory() { return stateManager_->getManagedMemory(); }

  /// @brief Lock the state
  void lock() { mutex_->lock(); }

  /// @brief Unlock the state
  void unlock() { mutex_->unlock(); }

 private:
  /// AbstractState manager setter
  /// @details Setter used by Hedgehog to indicate which state manager is currently using a specific state.
  /// @param stateManager AbstractState manager managing the state
  void stateManager(StateManager<Separator, AllTypes...> *stateManager) { stateManager_ = stateManager; }
};
}

#endif //HEDGEHOG_ABSTRACT_STATE_H
</file22>

<file23>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_STATE_MANAGER_H
#define HEDGEHOG_STATE_MANAGER_H

#include <utility>

#include "abstract_state.h"
#include "../../behavior/copyable.h"
#include "../../behavior/task_node.h"

/// @brief Hedgehog main namespace
namespace hh {

/// AbstractState manager
/// @brief
/// The state manager is a Hedgehog node that manages locally the state of the computation. To do so, it uses a state
/// protected by a mutex. The state holds the data structures that are used to manage the flow of data and organize
/// rendez-vous points or other synchronization mechanisms.
/// The default order of execution is:
///     -# The StateManager will acquire data,
///     -# The StateManager will lock the AbstractState
///     -# The StateManager will send the data to the AbstractState,
///     -# The compatible Execute::execute is called within the data,
///     -# During the call of Execute::execute, if the method StateMultiSenders::addResult is invoked the "result data"
/// is stored in a ready list,
///     -# When the Execute::execute has returned, the waiting list is emptied as output of the StateManager,
///     -# The StateManager will unlock the AbstractState.
///
/// The state is protected because it can be shared between multiple state managers, either with multiple state
/// managers in the same graph or if the state managers belongs to a graph that is duplicated with an execution
/// pipeline. In this case, each of the state managers in every graph copy will share the same state. This can be
/// used when dealing with computation across multiple GPUs, to synchronize data or share information between devices.
///
/// The state manager can be derived to change its termination rule for example. The method copyStateManager can be
/// derived to customise the copy mechanism of the state manager.
/// @attention A state manager can not be part of a group of threads (multi-threaded).
/// @attention In case of a cycle in the graph CanTerminate::canTerminate needs to be overloaded or the graph will
///// deadlock. By default, AbstractTask::canTerminate will be true if there is no "input node" connected AND no data
///// available in the task input queue (CF tutorial 3).
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
class StateManager
    : public behavior::TaskNode,
      public behavior::CanTerminate,
      public behavior::Cleanable,
      public behavior::Copyable<StateManager<Separator, AllTypes...>>,
      public tool::BehaviorMultiReceiversTypeDeducer_t<tool::Inputs<Separator, AllTypes...>>,
      public tool::BehaviorMultiSendersTypeDeducer_t<tool::Outputs<Separator, AllTypes...>> {
 private:
  std::shared_ptr<AbstractState<Separator, AllTypes...>> state_ = nullptr; ///< AbstractState managed
  std::shared_ptr<core::CoreStateManager<Separator, AllTypes...>>
      coreStateManager_ = nullptr; ///<AbstractState manager core

 public:
  /// @brief Main state manager constructor
  /// @param state AbstractState managed by the state manager
  /// @param name Name of the state manager (default: "AbstractState manager")
  /// @param automaticStart Flag to start the execution of the state manager without data (sending automatically nullptr
  /// to each of the input types)
  /// @throw std::runtime_error the state is not valid (== nullptr or does not derive from CoreStateManager)
  explicit StateManager(
      std::shared_ptr<AbstractState<Separator, AllTypes...>> state,
      std::string const &name = "State manager",
      bool const automaticStart = false)
      : behavior::TaskNode(
      std::make_shared<core::CoreStateManager<Separator, AllTypes...>>(this, state, name, automaticStart)),
        behavior::Copyable<StateManager<Separator, AllTypes...>>(1),
        tool::BehaviorMultiSendersTypeDeducer_t<tool::Outputs<Separator, AllTypes...>>(),
        state_(state) {
    if (state == nullptr) {
      throw std::runtime_error("The state given to the state manager should be valid (!= nullptr).");
    }

    if (auto
        coreStateManager = std::dynamic_pointer_cast<core::CoreStateManager<Separator, AllTypes...>>(this->core())) {
      coreStateManager_ = coreStateManager;
    } else {
      throw std::runtime_error("The core used by the state manager should be a CoreStateManager.");
    }
  }

  /// AbstractState Manager constructor with a user-custom core
  /// @brief A custom core can be used to customize how the state manager behaves internally. For example, by default
  /// any input is stored in a std::queue, it can be changed to a std::priority_queue instead through the core.
  /// @param core Custom core used to change the behavior of the state manager
  /// @param state AbstractState managed by the state manager
  /// @throw std::runtime_error the state is not valid (== nullptr or does not derive from CoreStateManager)
  explicit StateManager(
      std::shared_ptr<core::CoreStateManager<Separator, AllTypes...>> core,
      std::shared_ptr<AbstractState<Separator, AllTypes...>> state)
      : behavior::TaskNode(std::move(core)),
        behavior::Copyable<StateManager<Separator, AllTypes...>>(1),
        tool::BehaviorMultiSendersTypeDeducer_t<tool::Outputs<Separator, AllTypes...>>() {
    if (state == nullptr) {
      throw std::runtime_error("The state given to the state manager should be valid (!= nullptr).");
    }
    if (this->core() == nullptr) {
      throw std::runtime_error("The core given to the state manager should be valid (!= nullptr).");
    }
    if (auto
        coreStateManager = std::dynamic_pointer_cast<core::CoreStateManager<Separator, AllTypes...>>(this->core())) {
      coreStateManager_ = coreStateManager;
    } else {
      throw std::runtime_error("The core used by the state manager should be a CoreStateManager.");
    }
  }

  /// @brief Default destructor for the state manager
  ~StateManager() override = default;

  /// @brief AbstractState accessor
  /// @return AbstractState managed by the state manager
  std::shared_ptr<AbstractState<Separator, AllTypes...>> const &state() const { return state_; }

  /// @brief Automatic start flag accessor
  /// @return True if the state manager is set to automatically start, else false
  [[nodiscard]] bool automaticStart() const { return this->coreStateManager()->automaticStart(); }

  /// @brief Accessor to the core
  /// @return Core tot he state manager
  std::shared_ptr<core::CoreStateManager<Separator, AllTypes...>> const &coreStateManager() const {
    return coreStateManager_;
  }

  /// @brief Default termination rule, it terminates if there is no predecessor connection and there is no input data
  /// @return True if the state manager can terminate, else false
  [[nodiscard]] bool canTerminate() const override {
    return !coreStateManager_->hasNotifierConnected() && coreStateManager_->receiversEmpty();
  }

  /// @brief Provide a copy of the state manager
  /// @return A copy of the state manager
  /// @throw std::runtime_error a state manager copy is not valid (== nullptr or do not share the same state)
  std::shared_ptr<StateManager<Separator, AllTypes...>> copy() final {
    auto copy = copyStateManager(this->state_);
    if (copy == nullptr) {
      std::ostringstream oss;
      oss
          << "A copy of the state manager " << this->name() << " has been invoked but return nullptr. "
          << "Please implement the copyStateManager method to create a copy of the current state manager with the same state.";
      throw std::runtime_error(oss.str());
    }
    if (copy->state_ != this->state_) {
      std::ostringstream oss;
      oss << "A copy and the state manager \"" << this->name() << "\" do not share the same state.\n";
      throw std::runtime_error(oss.str());
    }
    return copy;
  }

  /// @brief Customizable copy method
  /// @param state AbstractState to insert in the state manager copy
  /// @return New state manager with the same state
  virtual std::shared_ptr<StateManager<Separator, AllTypes...>>
  copyStateManager(std::shared_ptr<AbstractState<Separator, AllTypes...>> state) {
    return std::make_shared<StateManager<Separator, AllTypes...>>(state, this->name(), this->automaticStart());
  }

};
}

#endif //HEDGEHOG_STATE_MANAGER_H
</file23>

<file24>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_ABSTRACT_ATOMIC_TASK_H
#define HEDGEHOG_ABSTRACT_ATOMIC_TASK_H

#include "abstract_task.h"
#include "../../core/implementors/concrete_implementor/slot/atomic_slot.h"
#include "../../core/implementors/concrete_implementor/receiver/atomic_queue_receiver.h"

/// @brief Hedgehog main namespace
namespace hh {

/// @brief Task using a communication layer (slot) and a queue to receive data using atomics
/// @details For more details, go to AbstractTask documentation
/// @warning This task cannot accept nullptr input data
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
class AbstractAtomicTask : public AbstractTask<Separator, AllTypes...> {
 public:
  /// @brief Create an AbstractAtomicTask
  /// @brief Construct a task with a name, its number of threads (default 1) and if the task should start automatically
  /// or not (default should not start automatically)
  /// @param name Task name
  /// @param numberThreads Task number of threads
  /// @param automaticStart Flag to start the execution of the task without data (sending automatically nullptr to each
  /// of the input types)
  /// @throw std::runtime_error the number of threads == 0 or the core is not of the right type (do not derive from CoreTask)
  explicit AbstractAtomicTask(std::string const &name,
                              size_t const numberThreads = 1,
                              bool const automaticStart = false)
      : hh::AbstractTask<Separator, AllTypes...>(
      std::make_shared<hh::core::CoreTask<Separator, AllTypes...>>(
          this,
          name, numberThreads, automaticStart,
          std::make_shared<hh::core::implementor::AtomicSlot>(),
          std::make_shared<hh::core::implementor::MAQR<Separator, AllTypes...>>(),
          std::make_shared<hh::tool::DME<Separator, AllTypes...>>(this),
          std::make_shared<hh::core::implementor::DefaultNotifier>(),
          std::make_shared<hh::tool::MDS<Separator, AllTypes...>>()
      )) {}

  /// @brief Default constructor creating a mono threaded task called "AtomicTask"
  AbstractAtomicTask() : AbstractAtomicTask("AtomicTask") {}
};

}

#endif //HEDGEHOG_ABSTRACT_ATOMIC_TASK_H
</file24>

<file25>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_ABSTRACT_CUDA_TASK_H
#define HEDGEHOG_ABSTRACT_CUDA_TASK_H
#ifdef HH_USE_CUDA

#include <cuda_runtime.h>
#include <unordered_set>

#include "abstract_task.h"
#include "../../tools/cuda_debugging.h"

/// @brief Hedgehog main namespace
namespace hh {

/// @brief Abstract Task specialized for CUDA computation.
/// @details At initialization, the device is set to the task (cudaSetDevice), and a stream is created and bound to the
/// task (cudaStreamCreate). During shutdown, the stream is destroyed (cudaStreamDestroy).
/// @par Virtual functions
/// Execute::execute (one for each of TaskInputs) <br>
/// AbstractCUDATask::copy (only used if number of threads is greater than 1 or used in an ExecutionPipeline) <br>
/// AbstractCUDATask::initializeCuda <br>
/// AbstractCUDATask::shutdownCuda <br>
/// Node::canTerminate <br>
/// Node::extraPrintingInformation <br>
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
class AbstractCUDATask : public AbstractTask<Separator, AllTypes...> {
 private:
  bool enablePeerAccess_ = false;               ///< Enable CUDA Peer Access through all CUDA devices available
  std::unordered_set<int> peerDeviceIds_ = {};  ///< Sparse matrix of linked CUDA devices
  cudaStream_t stream_ = {};                    ///< CUDA stream linked to the task

 public:
  /// @brief AbstractCUDATask full constructor
  /// @param name Task name
  /// @param numberThreads Number of threads for the task
  /// @param enablePeerAccess Enable peer access for NVIDIA GPUs
  /// @param automaticStart Flag for automatic start (Cf. AbstractTask)
  AbstractCUDATask(std::string const &name, size_t numberThreads, bool enablePeerAccess, bool automaticStart = false)
      : AbstractTask<Separator, AllTypes...>(name, numberThreads, automaticStart),
        enablePeerAccess_(enablePeerAccess) {
    this->coreTask()->printOptions().background({0x76, 0xb9, 0x00, 0xff});
    this->coreTask()->printOptions().font({0xff, 0xff, 0xff, 0xff});
  }

  /// @brief Main constructor for a AbstractCUDATask
  /// @param name Name of the AbstractCUDATask
  /// @param numberThreads Number of thread for this task (default 1)
  explicit AbstractCUDATask(std::string const name = "CudaTask", size_t numberThreads = 1) :
      AbstractCUDATask<Separator, AllTypes...>(name, numberThreads, false, false) {};

  /// @brief Custom core task constructor
  /// @param coreTask Custom core to use
  /// @param enablePeerAccess Enable per access for NVIDIA GPUs
  AbstractCUDATask(std::shared_ptr<hh::core::CoreTask<Separator, AllTypes...>> coreTask, bool enablePeerAccess)
      : AbstractTask<Separator, AllTypes...>(std::shared_ptr<hh::core::CoreTask<Separator, AllTypes...>>(coreTask)),
        enablePeerAccess_(enablePeerAccess) {
    this->coreTask()->printOptions().background({0x76, 0xb9, 0x00, 0xff});
    this->coreTask()->printOptions().font({0xff, 0xff, 0xff, 0xff});
  }

  /// @brief Default destructor
  ~AbstractCUDATask() override {
    if (this->memoryManager() != nullptr) {
      checkCudaErrors(cudaSetDevice(this->memoryManager()->deviceId()));
    }
  }

  /// @brief Initialize an AbstractCUDATask to bind it to a CUDA device, and do the peer access if enabled.
  /// At the end will call AbstractCUDATask::initializeCuda.
  void initialize() final {
    int numGpus = 0;
    int canAccess = 0;
    checkCudaErrors(cudaGetDeviceCount(&numGpus));
    assert(this->deviceId() < numGpus);
    checkCudaErrors(cudaSetDevice(this->deviceId()));
    checkCudaErrors(cudaStreamCreate(&stream_));

    if (enablePeerAccess_) {
      for (int i = 0; i < numGpus; ++i) {
        if (i != this->deviceId()) {
          checkCudaErrors(cudaDeviceCanAccessPeer(&canAccess, this->deviceId(), i));

          if (canAccess) {
            auto ret = cudaDeviceEnablePeerAccess(i, 0);
            if (ret != cudaErrorPeerAccessAlreadyEnabled) {
              checkCudaErrors(ret);
            }
            peerDeviceIds_.insert(i);
          }
        }
      }
    }
    auto ret = cudaGetLastError();
    if (ret != cudaErrorPeerAccessAlreadyEnabled) {
      checkCudaErrors(ret);
    }
    this->initializeCuda();
  }

  /// @brief Shutdown an AbstractCUDATask to destroy the task's CUDA stream created during
  /// AbstractCUDATask::initialize.
  /// First calls AbstractCUDATask::shutdownCuda.
  void shutdown() final {
    this->shutdownCuda();
    checkCudaErrors(cudaStreamDestroy(stream_));
  }

  /// @brief Virtual initialization step, where user defined data structure can be initialized.
  virtual void initializeCuda() {}

  /// @brief Virtual shutdown step, where user defined data structure can be destroyed.
  virtual void shutdownCuda() {}

  /// @brief Accessor for peer access choice
  /// @return True if peer access is enabled, else False
  bool enablePeerAccess() const { return enablePeerAccess_; }

  /// @brief Getter for CUDA task's stream
  /// @return CUDA stream
  cudaStream_t stream() const { return stream_; }

  /// @brief Accessor for peer access enabled for a specific device id
  /// @param peerDeviceId Device id to test
  /// @return True if peer access enable for device id peerDeviceId, else False
  bool hasPeerAccess(int peerDeviceId) { return peerDeviceIds_.find(peerDeviceId) != peerDeviceIds_.end(); }

};

}

#endif //HH_USE_CUDA
#endif //HEDGEHOG_ABSTRACT_CUDA_TASK_H
</file25>

<file26>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_ABSTRACT_LIMITED_ATOMIC_TASK_H
#define HEDGEHOG_ABSTRACT_LIMITED_ATOMIC_TASK_H

#include "abstract_task.h"
#include "../../core/implementors/concrete_implementor/slot/atomic_slot.h"
#include "../../core/implementors/concrete_implementor/receiver/limited_atomic_queue_receiver.h"

/// @brief Hedgehog main namespace
namespace hh {

/// @brief Task using a communication layer (slot) and a limited queue (LimitedAtomicQueueReceiver) to receive data
/// using atomics
/// @details For more details on the base, go to AbstractTask documentation.
/// @tparam MaxCapacity Queue maximum capacity
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<long long MaxCapacity, size_t Separator, class ...AllTypes>
class AbstractLimitedAtomicTask : public AbstractTask<Separator, AllTypes...> {
 public:
  /// @brief Create an AbstractLimitedAtomicTask
  /// @brief Construct a task with a name, its number of threads (default 1) and if the task should start automatically
  /// or not (default should not start automatically)
  /// @param name Task name
  /// @param numberThreads Task number of threads
  /// @param automaticStart Flag to start the execution of the task without data (sending automatically nullptr to each
  /// of the input types)
  /// @throw std::runtime_error the number of threads == 0 or the core is not of the right type (do not derive from CoreTask)
  explicit AbstractLimitedAtomicTask(
      std::string const &name, size_t const numberThreads = 1, bool const automaticStart = false)
      : hh::AbstractTask<Separator, AllTypes...>(
      std::make_shared<hh::core::CoreTask<Separator, AllTypes...>>(
          this,
          name, numberThreads, automaticStart,
          std::make_shared<hh::core::implementor::AtomicSlot>(),
          std::make_shared<hh::core::implementor::MLAQR<MaxCapacity, Separator, AllTypes...>>(),
          std::make_shared<hh::tool::DME<Separator, AllTypes...>>(this),
          std::make_shared<hh::core::implementor::DefaultNotifier>(),
          std::make_shared<hh::tool::MDS<Separator, AllTypes...>>()
      )) {}

  /// @brief Default constructor creating a mono threaded task called "LimitedAtomicTask"
  explicit AbstractLimitedAtomicTask() : AbstractLimitedAtomicTask("LimitedAtomicTask") {};
};

}

#endif //HEDGEHOG_ABSTRACT_LIMITED_ATOMIC_TASK_H
</file26>

<file27>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_ABSTRACT_MIXED_TASK_H
#define HEDGEHOG_ABSTRACT_MIXED_TASK_H

#include "abstract_task.h"
#include "../../core/implementors/concrete_implementor/slot/atomic_slot.h"

/// @brief Hedgehog main namespace
namespace hh {
/// @brief Task using a communication layer (slot) using atomics and a queue to receive data protected with mutex
/// @details For more details, go to AbstractTask documentation
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
class AbstractMixedTask : public hh::AbstractTask<Separator, AllTypes...> {
 public:
  /// @brief Create an AbstractMixedTask
  /// @brief Construct a task with a name, its number of threads (default 1) and if the task should start automatically
  /// or not (default should not start automatically)
  /// @param name Task name
  /// @param numberThreads Task number of threads
  /// @param automaticStart Flag to start the execution of the task without data (sending automatically nullptr to each
  /// of the input types)
  /// @throw std::runtime_error the number of threads == 0 or the core is not of the right type (do not derive from CoreTask)
  explicit AbstractMixedTask(std::string const &name,
                             size_t const numberThreads = 1,
                             bool const automaticStart = false)
      : hh::AbstractTask<Separator, AllTypes...>(
      std::make_shared<hh::core::CoreTask<Separator, AllTypes...>>(
          this,
          name, numberThreads, automaticStart,
          std::make_shared<hh::core::implementor::AtomicSlot>(),
          std::make_shared<hh::tool::MQR<Separator, AllTypes...>>(),
          std::make_shared<hh::tool::DME<Separator, AllTypes...>>(this),
          std::make_shared<hh::core::implementor::DefaultNotifier>(),
          std::make_shared<hh::tool::MDS<Separator, AllTypes...>>()
      )) {}

  /// @brief Default constructor creating a mono threaded task called "AtomicTask"
  AbstractMixedTask() : AbstractMixedTask("MixedTask") {}
};
}

#endif //HEDGEHOG_ABSTRACT_MIXED_TASK_H
</file27>

<file28>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_ABSTRACT_TASK_H
#define HEDGEHOG_ABSTRACT_TASK_H

#include <memory>
#include <string>
#include <ostream>
#include <utility>

#include "../../behavior/copyable.h"
#include "../../behavior/cleanable.h"
#include "../../behavior/task_node.h"
#include "../../behavior/multi_execute.h"
#include "../../behavior/input_output/multi_receivers.h"
#include "../../behavior/input_output/task_multi_senders.h"

#include "../../core/nodes/core_task.h"

/// @brief Hedgehog main namespace
namespace hh {

/// @brief Base node for computation
/// @details Hedgehog Graph's node made for processing data from the their overloaded execute method from
/// Execute::execute.
///
/// An AbstractTask can be bound to multiple threads, forming a group of tasks. The base AbstractTask will be copied n-1
/// times and each of them will be bound to a thread. The AbstractTask::copy method must be overloaded to use this
/// functionality. Also, if the AbstractTask is part of a Graph that will be duplicated with an AbstractExecutionPipeline,
/// AbstractTask::copy method needs to be overloaded.
///
/// A MemoryManager could be linked to a task:
/// @code
/// // Implementation of a basic Task
/// class StaticSizeTToManagedMemory : public hh::AbstractTask<1, size_t, StaticManagedMemory> {
/// public:
///  explicit StaticSizeTToManagedMemory(size_t numberThread = 1)
///      : hh::AbstractTask<1, size_t, StaticManagedMemory>("StaticManagedMemory", numberThread, false) {}
///  ~StaticSizeTToManagedMemory() override = default;
///
///  void execute([[maybe_unused]] std::shared_ptr<size_t> data) override {
///    this->addResult(std::dynamic_pointer_cast<StaticManagedMemory>(this->getManagedMemory()));
///  }
///
///  std::shared_ptr<hh::AbstractTask<1, size_t, StaticManagedMemory>> copy() override {
///    return std::make_shared<StaticSizeTToManagedMemory>(this->numberThreads());
///  }
/// };
///
/// // Implementation of a managed memory
/// class StaticManagedMemory : public hh::ManagedMemory {
///  int *array_ = nullptr;
/// public:
///  explicit StaticManagedMemory(size_t const sizeAlloc) { array_ = new int[sizeAlloc]; }
///  ~StaticManagedMemory() override { delete[] array_; }
/// };
///
/// // Instantiation and connection with a memory manager
/// auto staticTask = std::make_shared<StaticSizeTToManagedMemory>(2);
/// auto staticMM = std::make_shared<hh::StaticMemoryManager<StaticManagedMemory, size_t>>(2, 2);
/// staticTask->connectMemoryManager(staticMM);
/// @endcode
///
/// The default order of execution is:
///     -# The group is created, for each task:
///     -# Threads are spawned for each instance in the group,
///     -# The AbstractTask::initialize is called,
///     -# The memory manager, if it exists, is bound to the task (the device Id is shared, and is initialized),
///     -# Execute is called, while AbstractTask::canTerminate is True:
///         - If the task is set to start automatically Execute::execute is called with nullptr,
///         - If not, the task will wait for a data to come and Execute::execute is called with the received data,
///     -# AbstractTask::shutdown is called, and signals to the linked nodes to wake up.
///
/// Only Execute::execute method needs to be overloaded for each AbstractTask input type.
///
/// \par Virtual functions
///     - Execute::execute (one for each of TaskInputs) <br>
///     - AbstractTask::initialize <br>
///     - AbstractTask::shutdown <br>
///     - AbstractTask::copy (mandatory if usage of numberThreads greater than 1 or AbstractExecutionPipeline) <br>
///     - Node::canTerminate (mandatory if cycle in the graph) <br>
///     - Node::extraPrintingInformation
///
/// @attention In case of a cycle in the graph AbstractTask::canTerminate needs to be overloaded or the graph will
/// deadlock. By default, CanTerminate::canTerminate will be true if there is no "input node" connected AND no data
/// available in the task input queue (CF tutorial 3).
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template<size_t Separator, class ...AllTypes>
class AbstractTask
    : public behavior::TaskNode,
      public behavior::CanTerminate,
      public behavior::Cleanable,
      public behavior::Copyable<AbstractTask<Separator, AllTypes...>>,
      public tool::BehaviorMultiReceiversTypeDeducer_t<tool::Inputs<Separator, AllTypes...>>,
      public tool::BehaviorMultiExecuteTypeDeducer_t<tool::Inputs<Separator, AllTypes...>>,
      public tool::BehaviorTaskMultiSendersTypeDeducer_t<tool::Outputs<Separator, AllTypes...>> {
 private:
  std::shared_ptr<hh::core::CoreTask<Separator, AllTypes...>> const coreTask_ = nullptr; ///< Task core
 public:
  /// @brief Default constructor (Task with one thread named "Task")
  AbstractTask() : AbstractTask("Task", 1, false) {};

  /// AbstractTask main constructor
  /// @brief Construct a task with a name, its number of threads (default 1) and if the task should start automatically
  /// or not (default should not start automatically)
  /// @param name Task name
  /// @param numberThreads Task number of threads
  /// @param automaticStart Flag to start the execution of the task without data (sending automatically nullptr to each
  /// of the input types)
  /// @throw std::runtime_error the number of threads == 0 or the core is not of the right type (do not derive from CoreTask)
  explicit AbstractTask(std::string const &name, size_t const numberThreads = 1, bool const automaticStart = false)
      : behavior::TaskNode(std::make_shared<core::CoreTask<Separator, AllTypes...>>(this,
                                                                                    name,
                                                                                    numberThreads,
                                                                                    automaticStart)),
        behavior::Copyable<AbstractTask<Separator, AllTypes...>>(numberThreads),
        tool::BehaviorTaskMultiSendersTypeDeducer_t<tool::Outputs<Separator, AllTypes...>>(
            (std::dynamic_pointer_cast<hh::core::CoreTask<Separator, AllTypes...>>(this->core()))),
        coreTask_(std::dynamic_pointer_cast<core::CoreTask<Separator, AllTypes...>>(this->core())) {
    if (numberThreads == 0) { throw std::runtime_error("A task needs at least one thread."); }
    if (coreTask_ == nullptr) { throw std::runtime_error("The core used by the task should be a CoreTask."); }
  }

  /// Construct a task from a user-defined core.
  /// @brief A custom core can be used to customize how the task behaves internally. For example, by default any input
  /// is stored in a std::queue, it can be changed to a std::priority_queue instead through the core.
  /// @param coreTask Custom core used to change the behavior of the task
  explicit AbstractTask(std::shared_ptr<hh::core::CoreTask<Separator, AllTypes...>> coreTask)
      : behavior::TaskNode(std::move(coreTask)),
        behavior::Copyable<AbstractTask<Separator, AllTypes...>>(
            std::dynamic_pointer_cast<core::CoreTask<Separator, AllTypes...>>(this->core())->numberThreads()),
        tool::BehaviorTaskMultiSendersTypeDeducer_t<tool::Outputs<Separator, AllTypes...>>(
            std::dynamic_pointer_cast<hh::core::CoreTask<Separator, AllTypes...>>(this->core())),
        coreTask_(std::dynamic_pointer_cast<core::CoreTask<Separator, AllTypes...>>(this->core())) {
  }

  /// @brief Default task destructor
  ~AbstractTask() override = default;

  /// @brief Belonging graph id accessor
  /// @return  Belonging graph id
  [[nodiscard]] size_t graphId() const { return coreTask_->graphId(); }

  /// @brief Default termination rule, it terminates if there is no predecessor connection and there is no input data
  /// @return True if the task can terminate, else false
  [[nodiscard]] bool canTerminate() const override {
    return !coreTask_->hasNotifierConnected() && coreTask_->receiversEmpty();
  }

  /// @brief Automatic start flag accessor
  /// @return True if the task is set to automatically start, else false
  [[nodiscard]] bool automaticStart() const { return this->coreTask()->automaticStart(); }

 protected:
  /// @brief Accessor to the core task
  /// @return Core task
  std::shared_ptr<hh::core::CoreTask<Separator, AllTypes...>> const &coreTask() const { return coreTask_; }

  /// @brief Accessor to device id linked to the task (default 0 for CPU task)
  /// @return Device id linked to the task
  [[nodiscard]] int deviceId() const { return coreTask_->deviceId(); }
};
}

#endif //HEDGEHOG_ABSTRACT_TASK_H
</file28>

<file29>
// NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the
// software in any medium, provided that you keep intact this entire notice. You may improve, modify and create
// derivative works of the software or any portion of the software, and you may copy and distribute such modifications
// or works. Modified works should carry a notice stating that you changed the software and should note the date and
// nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the
// source of the software. NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR
// WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE
// CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS
// THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE. You
// are solely responsible for determining the appropriateness of using and distributing the software and you assume
// all risks associated with its use, including but not limited to the risks and costs of program errors, compliance
// with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of
// operation. This software is not intended to be used in any situation where a failure could cause risk of injury or
// damage to property. The software developed by NIST employees is not subject to copyright protection within the
// United States.

#ifndef HEDGEHOG_LAMBDA_TASK_H
#define HEDGEHOG_LAMBDA_TASK_H

#include "../../core/implementors/concrete_implementor/task/internal_lambda_task.h"


/// @brief Hedgehog main namespace
namespace hh {

/// @brief Type alias to the InternalLambdaTask
template <class SubType, size_t Separator, class ...AllTypes>
using ILT = core::implementor::InternalLambdaTask<SubType, Separator, AllTypes...>;

/// @brief Specialized lambda task interface (for user-defined lambda task)
/// @tparam SubType Type of the inheriting specialized lambda task (CRTP, void by default)
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template <class SubType, size_t Separator, class ...AllTypes>
class SpecializedLambdaTask : 
    public ILT<SubType, Separator, AllTypes...> {
 public:
  /// @brief Type alias to the lambda container type
  using Lambdas = tool::LambdaContainerDeducer_t<SubType, tool::Inputs<Separator, AllTypes...>>;

 public:
  /// @brief Construct a lambda task with a pointer to the subclass, a tuple of lambda functions, a name, its number of 
  ///        threads (default 1) and if the task should start automatically or not (default should not start automatically)
  /// @param self Pointer to the user-defined lambda task (CRTP)
  /// @param lambda Tuple of lambda functions (one function per input type of the task)
  /// @param name Task name
  /// @param numberThreads Task number of threads
  /// @param automaticStart Flag to start the execution of the task without data (sending automatically nullptr to each
  /// of the input types)
  /// @throw std::runtime_error the number of threads == 0 or the core is not of the right type (do not derive from CoreTask)
  explicit SpecializedLambdaTask(SubType *self, Lambdas lambdas, std::string const &name = "Task", size_t const numberThreads = 1,
          bool const automaticStart = false)
      : ILT<SubType, Separator, AllTypes...>(self, lambdas, name, numberThreads, automaticStart) {}

  /// @brief Construct a lambda task with the pionter to the subclass, a name, its number of threads (default 1) and if
  ///        the task should start automatically or not (default should not start automatically)
  /// @param self Pointer to the user-defined lambda task (CRTP)
  /// @param name Task name
  /// @param numberThreads Task number of threads
  /// @param automaticStart Flag to start the execution of the task without data (sending automatically nullptr to each
  /// of the input types)
  /// @throw std::runtime_error the number of threads == 0 or the core is not of the right type (do not derive from CoreTask)
  explicit SpecializedLambdaTask(SubType *self, std::string const &name = "Task", size_t const numberThreads = 1,
          bool const automaticStart = false)
      : SpecializedLambdaTask<SubType, Separator, AllTypes...>(self, {}, name, numberThreads, automaticStart) {}

  /// @brief A custom core can be used to customize how the task behaves internally. For example, by default any input
  ///        is stored in a std::queue, it can be changed to a std::priority_queue instead through the core.
  /// @param self Pointer to the lambda task
  /// @param coreTask Custom core used to change the behavior of the task
  explicit SpecializedLambdaTask(SubType *self, std::shared_ptr<core::implementor::LambdaCoreTask<SubType, Separator, AllTypes...>> coreTask) 
      : ILT<SubType, Separator, AllTypes...>(self, coreTask) {}
};

/// @brief Default lambda task (there is no subtype so it shouldn't be specified)
/// @tparam Separator Separator position between input types and output types
/// @tparam AllTypes List of input and output types
template <size_t Separator, class ...AllTypes>
class LambdaTask
    : public ILT<LambdaTask<Separator, AllTypes...>, Separator, AllTypes...> {
 public:
  /// @brief Type alias to the lambda container type
  using Lambdas = tool::LambdaContainerDeducer_t<LambdaTask<Separator, AllTypes...>, tool::Inputs<Separator, AllTypes...>>;

 public:
  /// @brief Construct a lambda task with a tuple of lambda functions, a name, its number of threads (default 1) and if
  ///        the task should start automatically or not (default should not start automatically)
  /// @param lambda Tuple of lambda functions (one function per input type of the task)
  /// @param name Task name
  /// @param numberThreads Task number of threads
  /// @param automaticStart Flag to start the execution of the task without data (sending automatically nullptr to each
  /// of the input types)
  /// @throw std::runtime_error the number of threads == 0 or the core is not of the right type (do not derive from CoreTask)
  explicit LambdaTask(Lambdas lambdas, std::string const &name = "Task", size_t const numberThreads = 1,
          bool const automaticStart = false)
      : ILT<LambdaTask<Separator, AllTypes...>, Separator, AllTypes...>(this, lambdas, name, numberThreads, automaticStart) {}

  /// @brief Construct a lambda task with a tuple of lambda functions, a name, its number of threads (default 1) and if
  ///        the task should start automatically or not (default should not start automatically)
  /// @param lambda Tuple of lambda functions (one function per input type of the task)
  /// @param name Task name
  /// @param numberThreads Task number of threads
  /// @param automaticStart Flag to start the execution of the task without data (sending automatically nullptr to each
  /// of the input types)
  /// @throw std::runtime_error the number of threads == 0 or the core is not of the right type (do not derive from CoreTask)
  explicit LambdaTask(std::string const &name = "Task", size_t const numberThreads = 1, bool const automaticStart = false)
      : LambdaTask<Separator, AllTypes...>({}, name, numberThreads, automaticStart) {}

  /// @brief A custom core can be used to customize how the task behaves internally. For example, by default any input
  ///        is stored in a std::queue, it can be changed to a std::priority_queue instead through the core.
  /// @param self Pointer to the lambda task
  /// @param coreTask Custom core used to change the behavior of the task
  explicit LambdaTask(std::shared_ptr<core::implementor::LambdaCoreTask<void, Separator, AllTypes...>> coreTask) 
      : ILT<LambdaTask<Separator, AllTypes...>, Separator, AllTypes...>(this, coreTask) {}
};

}

#endif //HEDGEHOG_LAMBDA_TASK_H
</file29>

</API>



<PAPERS>

<paper1>
Page 1:
Hedgehog: Understandable Scheduler-Free Heterogeneous Asynchronous Multithreaded Data-Flow Graphs

Alexandre Bardakoff∗†¶, Bruno Bachelet †, Timothy Blattner ∗, Walid Keyrouz∗, Gerson C. Kroiz § and Lo¨ıc Yon‡

∗National Institute of Standards & Technology, Gaithersburg, MD 20899-8970, email: ﬁrst.last@nist.gov

†Universit´e Clermont Auvergne, CNRS, LIMOS, F-63000 Clermont-Ferrand, France ‡ISIMA, CNRS, LIMOS, F-63000 Clermont-Ferrand, France

§Department of Mathematics and Statistics, University of Maryland, Baltimore County, Baltimore, MD 21250, USA ¶Corresponding author

Abstract—Getting performance on high-end heterogeneous nodes is challenging. This is due to the large semantic gap between a

computation’s speciﬁcation—possibly mathematical formulas or an abstract sequential algorithm—and its parallel implementa-

tion; this gap obscures the program’s parallel structures and how it gains or loses performance. We present Hedgehog, a library

aimed at coarse-grain parallelism. It explicitly embeds a data- ﬂow graph in a program and uses this graph at runtime to drive

the program’s execution so it takes advantage of hardware par- allelism (multicore CPUs and multiple accelerators). Hedgehog

has asynchronicity built in. It statically binds individual threads to graph nodes, which are ready to ﬁre when any of their inputs

are available. This allows Hedgehog to avoid using a global scheduler and the loss of performance associated with global

synchronizations and managing of thread pools. Hedgehog pro- vides a separation of concerns and distinguishes between compute

and state maintenance tasks. Its API reﬂects this separation and allows a developer to gain a better understanding of performance

when executing the graph. Hedgehog is implemented as a C + +17 headers-only library. One feature of the framework is its low

overhead; it transfers control of data between two nodes in ≈ 1 µs. This low overhead combines with Hedgehog’s API to provide

essentially cost-free proﬁling of the graph, thereby enabling experimentation for performance, which enhances a developer’s

insight into a program’s performance. Hedgehog’s asynchronous data-ﬂow graph supports a data

streaming programming model both within and between graphs. We demonstrate the effectiveness of this approach by highlighting

the performance of streaming implementations of two numer- ical linear algebra routines, which are comparable to existing

libraries: matrix multiplication achieves >95 %of the theoretical peak of 4 GPUs; LU decomposition with partial pivoting starts

streaming partial ﬁnal result blocks 40× earlier than waiting for the full result. The relative ease and understandability

of obtaining performance with Hedgehog promises to enable non-specialists to target performance on high-end single nodes. I. I NTRODUCTION

Parallel programs are increasing in complexity as they target massively parallel platforms (e.g., 2 × 64 or more CPU cores

and multiple GPUs). Obtaining performance on such platforms is challenging because of the large semantic gap between

a computation’s speciﬁcation and its implementation. The speciﬁcation is often as simple as a set of mathematical

formulas or an abstract sequential algorithm. By contrast, a parallel implementation must address several coupled issues

beyond what a sequential implementation addresses: concur- rent computations, multiple memory resources, race conditions

and deadlocks, and data motion costs. One approach to bridge this gap is to use a framework that simpliﬁes application

development and, equally important, exposes abstractions that address parallelism and performance as ﬁrst-class concerns.

Furthermore, these abstractions should represent parallel con- structs and make it easier to instrument and reason about an

application’s performance thereby allowing developers to gain deeper insight. This paper presents Hedgehog, a general-purpose

performance-oriented library aimed at coarse-grain parallelism on single high-end heterogeneous compute nodes. A Hedgehog

program contains an explicit representation of a static data- ﬂow graph. The graph executes in a pure asynchronous

data-driven mode without a global scheduler and statically binds threads to persistent tasks in the graph. Hedgehog

provides a separation of concerns and distinguishes between compute tasks (i.e., compute-bound kernels) and state

manager tasks. State managers represent and manage local states between the compute tasks that they connect to.

Hedgehog also provides a memory manager tool to control the use of memory resources within a task.

Hedgehog transfers control of data efﬁciently between two tasks ( ≈ 1 µs). Its explicit data-ﬂow representation and the

graph’s cost-free proﬁling allow the developer to quickly iden- tify how the overall computation is carried out. In addition, it

encourages a developer to experiment with the data-ﬂow graph itself and with how to customize the degree of parallelism of compute tasks.

Page 2:
The rest of this paper is organized as follows. Section II presents solution requirements. Section III reviews existing ap-

proaches and frameworks. Section IV discusses Hedgehog and provides a high-level view of its implementation. Section V

examines two linear algebra examples using Hedgehog and highlights obtained performances. Section VI concludes and Section VII outlines future work.

II. S OLUTION APPROACH Developing an application to scale on a high-end heteroge- neous node is challenging. These nodes have a high degree

of hardware parallelism with high core-count CPUs (currently 2× 64-core CPUs, 128-core CPUs soon), multiple accelerators

and GPUs (up to 4 or 8 per node), and multi-instance GPUs (7× per Nvidia A100 GPU). Furthermore, these nodes have

become commodity and, as such, are now accessible to a broad community that is much disconnected from the traditional

HPC community and lacks its deep knowledge, which is needed to take advantage of these nodes. An enabling solution

for this nascent HPC community should compose optimized compute kernels and efﬁcient data transfers between memory

domains (CPU and GPU), express the locality of data, overlap data motion and computations, and fully utilize available

hardware. Equally important, this solution should have an explicit and understandable program and execution model that

is accessible to both expert and non-expert developers so they can improve their code’s performance. This model will allow

developers to operate at higher levels of abstractions and will also make it easier for them to adapt their software designs to

future architectures as hardware evolves. Existing approaches can exploit the compute power available

in high-end nodes, but do so with an implicit execution model that requires the use of external proﬁling tools to reveal the

impact of software design decisions on performance. This makes it challenging for developers to reason about optimiza-

tion strategies. Furthermore, these external tools may have substantial overhead; this may make it even more challenging

for developers to pinpoint performance bottlenecks. Our solution, Hedgehog, is based on a static and explicit

data-ﬂow graph that operates without a global scheduler and is aimed at coarse-grain parallelism. The execution model

obtains performance via data pipelining strategies, which works best with streaming data. Using this approach, the

developer can effectively overlap data motion and computa- tions to keep the hardware busy. The model is accompanied

by tools that assist with memory management to express data locality in multiple memory domains (CPU and GPUs),

thereby addressing memory constraints on a heterogeneous node. We use the explicit representation throughout the ex-

ecution and proﬁling of the program; this leads to cost-free visual feedback. The representation and feedback make it

easier to reason about the graph’s execution and encourage the developer to experiment with the graph so as to optimize its

performance. This experimentation can lead to quickly iden- tifying the performance critical path in an implementation’s

graph. We designate this approach as portable designs for performance because the underlying data-ﬂow graph can be

easily tuned to different high-end nodes. These decisions can be analyzed in conjunction with the graph proﬁling to identify

optimal conﬁgurations. This iterative optimization approach also applies to improving tasks to take better advantage of

hardware, also called experimentation for performance. III. B ACKGROUND /STATE OF THE ART

Multiple models exist for developing parallel applications that maximize the utilization of available hardware and can target

future heterogeneous nodes. The three most commonly used approaches are parallel libraries, language extensions, and task-based libraries.

Parallelized libraries, such as OpenBLAS [22], OpenCV [6], or FFTW [8], implement parallelism within each function call

and effectively establish a synchronization barrier at the end of each function invocation in the parallelized library. Hedgehog

encourages the use of parallelized libraries in single-threaded mode within its tasks for their optimized implementations that

use hardware vector instructions for example. Directive-based approaches, such as OpenMP [18], OpenACC

[10], and OmpSs-2 [16] use mostly pragmas or codelets. These approaches focus on using loop parallelism to obtain perfor-

mance. They offer many options to customize the pragmas, which can become very complex when handling loops with

multiple dependencies and synchronization points. Therefore, to be used correctly, they often require power users with a

deep understanding of the hardware and have knowledge about such parallel programming techniques. The data-ﬂow model

is capable of fully utilizing a high-end node by orchestrating coarse-grain task parallelism. It also allows an end-user to

invoke parallel directive-based kernels from existing libraries in a task. Task-based approaches exist under numerous forms with dif-

ferent properties. The majority of task-based libraries operate with two prevalent traits: (1) the graph’s representation as a

DAG (Directed Acyclic Graph) and (2) the usage of a pool of threads. The programmer describes the DAG by specifying

dependencies between tasks, which task is applicable to either a processor, co-processor, or both. Efﬁciently binding these

tasks to threads in the thread pool, which also selects either the processor or co-processor as the compute resource, is non-

trivial. There is no perfect dynamic matching algorithm, which is considered a NP-complete problem, but optimizers can be

used to improve the matching. Furthermore, to speed up the overall computation, many task-based approaches add work-

stealing or work-balancing techniques at the coast of inscreas- ing overhead. These steps deﬁne how the library intrinsically

works, and are hidden from the algorithm developer in the interest of simplifying parallel programming.

Existing task-based libraries, such as HPX [11], Legion [2], StarPU [1] or Charm++ [12], target performance at any scale

from ﬁne-grained parallelism to distributed parallel computing.

Page 3:
HPX uses an API compatible with the C + + 14 standard and is based on message-driven computations and asynchronous

calls. Legion bases its computation representation on the decomposition of its data. The logical regions express locality

and dependence of program data and tasks that act on the logical regions. StarPU uses a codelet approach. Charm++

is a message-driven library that depends on asynchronous calls. Hedgehog focuses on maximizing hardware utilization

on a single node, while maintaining low latency, from 1 µs to 10 µs for a large variety of tasks. Tasks are represented as

C+ +classes that embed useful information for the computation (class attributes, static variables, usage of input/output streams)

as opposed to using codelets. Specialized libraries, such as Uintah [15], Kokkos [4], or

Halide [19], have been developed with key design decisions for speciﬁc application classes. Uintah is based on adaptive mesh

reﬁnement with a runtime system aimed at solving partial dif- ferential equations in large scale simulations. Kokkos, a library

used for manycore parallelism on clusters with MPI, targets HPC applications. It also comes with a co-library, kokkos-

kernel, specialized for linear algebra. Halide, a language em- bedded in C+ +, targets image processing algorithms. Hedgehog

has no specialization, but beneﬁts most from an effective coarse-grained data decomposition that feeds sufﬁcient data into the data-ﬂow graph.

Intel Threading Building Blocks [14] is a template library for parallel programming. It proposes an algorithm as skeletons

along with parallel containers to achieve performance on general algorithms. An algorithm is automatically represented

internally as a graph with the library in charge of managing the algorithm’s graph from creation to tear-down with work

stealing for load-balancing on the node. Hedgehog uses an explicit graph to construct the algorithm and maintains it

during execution. No scheduling or balancing are used because Hedgehog relies only on its data-ﬂow representation.

Hedgehog evolved from HTGS [3]; they are a part of task- based approach with some major differences explained in Sec-

tion IV. Hedgehog is at least as efﬁcient as HTGS, according to a study conducted in Section V-A. There is no loss of features;

instead some features have been added such as multiple inputs, broadcast, and an internal re-architecture transforming the

HTGS Bookkeeper into the State Manager. IV. H EDGEHOG Hedgehog is a software infrastructure that presents an al-

gorithm at a high level of abstraction and helps developers reason about their applications. The library is header-only and

implemented using the C + +17 standard, and requires no other external dependencies. Algorithms are formulated into a data-ﬂow graph using the

Hedgehog library. Nodes in the graph are persistent entities that accept and produce data. Edges connect nodes using queues that store data.

Nodes in Hedgehog have been designed for non-overlapping usage to achieve a separation of concerns. A task is a node

that carries out computations, where each task is statically bound to a thread. The state manager is a specialized task

that embeds a shareable thread-safe state object to locally manage and do synchronization on the computation ﬂow. This

separation of concerns is a cornerstone of Hedgehog’s design and facilitates the programmability of the library. The nodes

and edges operate without any added scheduler and, alongside the threads attached to each task, formulate an asynchronous

data pipeline, which allows Hedgehog to overlap computation, data motion, and I/O. It leverages streaming execution using

data decomposition to maximize the system utilization. The graph is also a node and can be embedded in another

graph; this structure enables composition and code sharing. The Hedgehog graph is static so there is no back-end reorga-

nization or expansion of the graph. To present Hedgehog and its model, we ﬁrst present the

data-ﬂow model in Section IV-A, with the different kinds of nodes in Section IV-B and their interfaces in Section IV-C.

Section IV-D uncovers our threading model and how the computation is conducted without a scheduler. Section IV-E

and Section IV-F reveals tools embedded in Hedgehog such as the memory manager, and our cost-free visual feedback.

Section IV-G exposes how Hedgehog enforces type compati- bility with C+ +metaprogramming techniques.

To illustrate the various components of the Hedgehog library, we present a CPU-based implementation of matrix multiplica-

tion. In Section V, we present the results of a variant of this implementation that targets multi-GPU nodes to showcase the

performance and low overhead of Hedgehog’s operation. To be clear, Hedgehog is a general purpose library; its programming

model has been used in a variety of applications such as image processing and signal processing.

In this example of matrix multiplication, we will create a BLAS-like routine, similar to GEneral Matrix Multiplication

(GEMM), C = A × B + C with matrices An×m, Bm×p, and Cn×p. These matrices are decomposed into blocks: C

is decomposed into N × P blocks along the rows and columns of the matrix, respectively. In order to access a

block at row r and column c we use the notation Cr,c. The computation is achieved by iterating for each block in C, Cr,c = ∑M

i=1(Ar,i × Bi,c), where M is the number of blocks along the shared dimension. This example as well as others

are available on github [9]. These tutorials demonstrate the API. A. Structural model: data-ﬂow graph

The ﬁrst step to programming with Hedgehog is to understand how data ﬂows within an algorithm. The best way to approach

this step is to formulate the algorithm as a data-ﬂow graph, which is a representation for computation using a directed

graph. The graph’s nodes are the computation actors and the

Page 4:
graph’s edges are the directed information ﬂow. The graph has one entry point and one exit point.

Every task executes based on the presence of data in its input queues, which results in a pipeline that executes concurrently.

This threading model is described with more detail in Sec- tion IV-D. Figure 1 shows the structure for the matrix multiplication data-

ﬂow graph, where circles are the tasks and diamonds are the state managers, can be split into the following computational steps:

1) The source (a) of the graph dispatches blocks of matrices A, B, and C to the input nodes. 2) The StateAB (b) accepts blocks of A and B, groups

them into compatible pairs of blocks, and emits pairs of compatible blocks. 3) The MatMul (c) task accepts pairs of A and B blocks,

applies matrix multiplication on them, and produces partial results P. 4) The StatePC (d) produces a PairPC output when it

receives one BlkC and one BlkP that need to be ac- cumulated. 5) The Acc (e) task accumulates the appropriate C blocks with the P blocks.

6) The StateC (f) produces an output when BlkC is fully accumulated. using MatrixType = float;// Type of Matrix elements

Order Ord = Order::Column;// Matrix orientation // Tasks auto matMulTask = std::make_shared<MatMul<MatrixType, Ord>>( ↪→numberThreadProduct, p);

auto accTask = std::make_shared<AccTask<MatrixType, Ord>>( ↪→numberThreadAddition); //[...] // Build the graph matMulGraph.input(stateAB);

matMulGraph.input(statePC); matMulGraph.addEdge(stateAB,matMulTask); matMulGraph.addEdge(matMulTask,statePC); matMulGraph.addEdge(StatePC,accTask);

matMulGraph.addEdge(accTask,statePC); matMulGraph.addEdge(accTask,stateC); matMulGraph.output(stateC); Listing 1: Simpliﬁed MatMul main

The Hedgehog Graph adds these tasks by estab- lishing an edge between them with the method graph.addEdge(SenderNode, ReceiverNode),

which will automatically generate FIFO (First In First Out) data queues. Methods from the graph connect tasks

to the inputs using graph.input(InputNode) and outputs using graph.output(OutputNode) as shown in Listing 1. B. Hedgehog nodes

Hedgehog provides several distinct types of nodes that are used to develop data-ﬂow graphs. The nodes are designed to

provide speciﬁc functionality in order to achieve a separa- tion of concerns approach; i.e., nodes that speciﬁcally target

state maintenance, computation, composition, or scalability. Each node type is restricted to consuming multiple input

types and producing a single output type, as described in Section IV-C. The node classes form a hierarchy to enable

expanding upon the Hedgehog library, as shown in Fig- ure 2. The available Hedgehog node types are (1) Graph,

(2) AbstractTask, (3) StateManager, (4) CUDATask, and (5) ExecutionPipeline. Node is the pure abstract class at the root of the class hierachy;

it is the base class for all Hedgehog node objects. The Graph object represents a computation, it connects a set of consistent

nodes and edges to carry out the computation. In Hedgehog, a node must be associated with a parent graph, which binds

its constituent nodes to the same device to improve data locality. The AbstractTask node operates on data; it is abstract as it

does not have an implementation for the execute methods of all input types. execute method is called with data that is taken

from the task’s input queue(s). It executes a computational kernel on the data it receives as shown in Figure 3. This ﬁgure

shows the execution logic of an AbstractTask, and displays the customization points. The canTerminate function identiﬁes

when to stop a task; by default, this is when there are no input nodes connected and nothing in the input queues. This

behavior can be modiﬁed to break cycles in the graph. The initialize and shutdown functions are called once to carry out

pre- or post- computation. Listing 2 for a simpliﬁed MatMul task, which implements the execute method to carry out the

matrix multiplication operation. class MatMul : public AbstractTask<BlkP, pair<BlkA, BlkB>>{ private: size_t count_ = 0; public:

MatMul(size_t nbThreads, size_t count) : AbstractTask<BlkP, pair<BlkA, BlkB>( "Product Task", nbThreads), count_(count){}

void execute(pair<BlkA,BlkB> ptr){ auto matA = ptr.first; auto matB = ptr.second; BlkP res {}; // res <- matA*matB cblas_sgemm(matA, matB, res);

this->addResult(res); } }; Listing 2: Simpliﬁed version of MatMul task The ﬁrst specialized AbstractTask is the StateManager. The

StateManager holds a State instance. The State expresses a localized state between two or more nodes. Once an input

data is available, the StateManager locks the State it owns and transfers the data to the State. Once the State computation

is done, its output data are gathered by the StateManager,

Page 5:
Source (a) StateAB (b) MatMul A × B = P (c) StatePC (d) Acc (e) StateC (f)BlkA BlkB BlkC PairAB BlkP PairPC BlkC BlkC BlkC

Figure 1: Matrix multiplication data-ﬂow graph Node Receives different types of input data, sends one type of output data. Graph Organized

structure of nodes. AbstractTask Processes received data. Can be multi-threaded. CUDATask Specialized Task for CUDA GPU, bound to a GPU. StateManager

Interacts with locked State. Restricted to one thread. ExecutionPipeline Duplicates a Graph. Customizes routing data to the graphs. State

Shareable thread-safe object. Useful to expresslocal state. Figure 2: UML simpliﬁed class hierarchy of Hedgehog

the State is unlocked and the gathered data are sent to its connected nodes. The shareableState object contains a mutual exclusion context

to ensure it is only accessed by one thread at a time. Both the StateManager and State are fully customizable, but operate

with the distinct requirement that StateManager is the only type of task in the graph that should express the state of a computation.

The second specialized AbstractTask is the CUDATask. It binds the task’s thread to a CUDA-enabled GPU, which is

done automatically by Hedgehog through a customization of the initialize function. This is used to streamline executing a

CUDA kernel, such as by automatically enabling CUDA peer- to-peer access and creating acudaStream for each instance of the CUDATask.

The last specialized task in Hedgehog is theExecutionPipeline which is used to simplify multi-GPU programming or other

execution contexts. This task creates mirror copies of a graph and distributes data between graph copies according to a

developer-speciﬁed strategy. Each graph copy is bound to a separate GPU; the graph’s data will be local to its tasks and,

as such, to the GPU that it binds to. When aStateManager is initializestart can terminate? shutdown notify all terminated wait can terminate? or data

available can terminate? lock queue get data from queue unlock queue execute (data) [True] [False] notiﬁcation [True] [False] [True] [False]

Conditional Step Customizable conditional Customizable step Figure 3: Task’s main runtime steps

copied, its State instance is shared across all StateManager instances. This is often used to share data across multiple

graphs, and potentially between GPUs. For example, data that is stored within theState can be retrieved and used by another

graph from itsStateManager. This data may reside in another GPU’s memory. It is up to the developer to initiate GPU-to-

GPU copying or direct peer access. Hedgehog is extensible; a specialized task can inherit from

AbstractTask to create tasks, for example specialized for AMD GPUs using OpenCL or other libraries. C. Nodes input and output data types

Nodes deﬁne their input and output types explicitly as template parameters (bound at compile-time) to ensure consistency. The

input and output types of two nodes must match in order to

Page 6:
connect them by an edge in the Hedgehog graph. Establishing this edge connection will automatically create the queues that

are used to store data between the two nodes. A node is restricted to a single output type and can have multiple input

types. The input and output types can be anything including types created by a user. For example, if a graph’s node requires

multiple output types, then these types can be gathered into a single class/struct. The input data types each have their own

independent queue. The output of a task can connect to zero or more inputs of other tasks. Data that is sent out of a task is

shared with all of its successor tasks. Hedegehog uses smart pointers to avoid the need for a deep copy. Data races that

may result from multiple tasks receiving the same pointer are not controlled by the library. It is important for end-users to

be aware of their usage patterns on received data. For example, the accumulate (Acc) task in the matrix multipli-

cation data-ﬂow graph from Figure 1 contains a single input and two output edges. Instantiating this task using Hedgehog is

done by specifying PairPC as the input type and BlkC as the output type for the node. An edge is then added from StatePC

to the Acc, and from Acc to both StateC and StatePC . The edges will create queues for each of these nodes, if they were

not already created, and any data thast is produced from the Acctask will be shared with the StateC and StatePC tasks. In

addition, the canTerminate function will need to be customized for the StatePC or Accnodes to break the cycle in the graph

as will be discussed in the next section. D. Threading model A graph begins processing data when the graph is executed,

which creates a thread for each task in the graph. If a task requests multiple threads (such as MatMul which accepts the

number of threads at construction as shown in Listing 2), then custom copies of the task are made using the user-overloaded

copy method. The original task and its copies form a task group, where each task in the group is statically bound to a

different thread. They share the same input and output edges consisting of queues and synchronization contexts. This forms

contention on the input queues, but also offers higher through- put when sufﬁcient data is waiting to be processed.

Hedgehog uses monitor synchronization to operate the edges; a consumer task holds a mutex and will enter the wait state

if its input queue is empty. The monitor is implemented with a std::condition variable. It will suspend the execution of the

thread if no input data is available. The thread will wake up when notiﬁed by another node, this occurs when termination

is requested or input data becomes available. When the thread is waiting for data, it will not consume CPU resources. If data

is available, then the thread will remove it from its queue. A producer task sends data and signals to its successor consumer

task, which transitions the successor consumer task from the wait state to the running state. The running and wait states

of a consumer task are managed entirely by the operating system. After a context switch, the signaled consumer task

will retrieve the data from its input queue and call its user- deﬁned execute function on the received data. A consumer

task can avoid the wait state and potentially the context switch if data were already available in its queue. A consumer task

in Hedgehog inﬁnitely fetches data from its input or waits until its canTerminate function returns true; by default this

happens when the input connection is terminated and the queue is empty. When termination occurs, the terminated task will

signal to all other tasks in the same group to wake-up and terminate properly. Selecting the degree of parallelism for a task helps improve

CPU utilization when executing the graph. For example, in matrix multiplication, the MatMul task can operate with the

number of threads equal to the physical core count, whereas the accumulation task can operate with a fraction of the

number of physical cores because it is less computationally complex. Specifying a good balance between the number of

physical cores and the number of copies of a task can help prevent over-subscription of the CPU for compute intensive

tasks, assuming there is enough data waiting to be processed in the task’s input queue. In our experience, over-subscription

rarely occurs due to the nature of the data-ﬂow approach and how tasks will enter a running state only when data is present

in a graph with dozens of independent tasks and edges. This behavior may vary depending on the nature of the algorithm.

Furthermore, developers ﬁnd the idea of tuning the number of threads understandable. E. Memory management

Memory management is often needed when GPU computa- tions or limitations due to hardware are involved. Hedgehog

implements a memory manager, a tool used by tasks. An instance of a memory manager can be created with a speciﬁc

data type and then attached to a task. This memory manager instance is thread-safe and limits the amount of data being

produced by the task. If the task is copied, such as when building a task group, then all tasks in the group will share the same memory manager.

A memory manager creates a ﬁxed-size pool of user-speciﬁed data buffers when the task is initialized. During a task’s

execute invocation, the task can fetch memory from this pool and will block if the pool is empty. The API provides a

mechanism to recycle memory back to the memory manager, which will add memory back into the pool and signal to a

task that is waiting. This allows a waiting task to obtain the needed memory and resume execution. The recycle mechanism

provides two steps: (1) complete the allocation-deallocation cycle to eliminate memory leaks and (2) update the state of

the memory. The state is updated when memory is returned to a memory manager. The state of memory indicates when a

memory buffer is ready to be recycled. If the memory is not ready to be recycled, then it will not be added to the memory

pool. This functionality is useful to indirectly express memory locality, such as to keep memory resident on GPUs to avoid

unnecessary data transfers.

Page 7:
Two types of memory managers exist: static and dynamic. Both managers will ﬁll the pool with objects during task

initialization. The dynamic memory manager will call the default constructor for the data objects whereas the static one

will call a specialized constructor. F . Proﬁling Hedgehog provides proﬁling through a printer class. It is

used to represent the current state of the graph. To measure the overhead of proﬁling, we compare the performance of

Hedgehog’s ﬁrst tutorial, the Hadamard product [20], with and without proﬁling, and execute it 1000 times on 16k × 16k

matrices and 2k× 2k blocks, as shown in Figure 4. To measure the impact of the proﬁling, we propose the following statistical analysis.

Let X1 and X2 be the execution times with and without proﬁling, respectively. Given the high number of experiments

and the central limit theorem, the experimental averages, X1 and X2, follow a normal distribution. Now deﬁne the stochastic variable X as X1 − X2√ S2

1 N + S2 2 N . X follows a normal distribution of expectation µ1 − µ2 and variance σ2 = 1. Let S2 1 and S2 2 be estimators of σ2 1 and σ2 2.

For the null hypothesis to hold, we propose µ1 = µ2; there is on average no statistical difference between a computation

with and without proﬁling. X becomes a standard normal distribution. The size of our sample is N = 1000. For this sample, the values

of X1 and X2 are respectively x1 = 1742.28 msand x2 = 1743.06 msand the estimations of the variances σ2 1 and σ2 2 are respectively s2

1 = 14.03 msand s2 2 = 12.49 ms. With this sample, the value of Xis x= −1.32, whose p-value is 0.4066.

These results allow us to accept the null hypothesis. We can therefore conclude that the average execution runtimes,

with or without proﬁling, do not differ signiﬁcantly. We believe this is because we gather performance metrics at the node

level, which is far less intensive than ﬁne-grained proﬁling approaches, such as measuring all function invocations.

The metrics gathered from the nodes are the execution time, waiting time, and queue usage. Additionally, the graph gathers

the creation and total execution times. This information can be presented in various ways depending on options chosen by

developers; for example, a task group can be expanded to show the performance of each thread. It is also possible to bind the

graph to one or multiple POSIX signals with a graph signal handler to capture them and generate the state of the graph at

that instant, such as when a segmentation fault occurs. A DOT ﬁle printer has been developed to generate Graphviz

[7] DOT ﬁles. The developer can use this visualization to understand how tasks and graphs interact with each other and

using this representation can immediately recognize the critical 1,720 1,740 1,760 1,780 1,800 1,820 0 50 100 150 200 250 Execution time bins ( ms)

Number of experiments Without proﬁling X2 With proﬁling X1 Figure 4: Hedgehog Tutorial 1 execution time distribution for

1000 experiments on 16k× 16k matrices and 2k× 2k blocks with and without proﬁling on a Mac Book Pro Mid 2015

path of the computation. Example DOT ﬁles can be found at the end of each of the Hedgehog tutorials [20]. G. Type checking

Hedgehog uses template metaprogramming to check the data- ﬂow graph consistency at compile-time. It achieves static

checking via constructs that use C + + 17 metafunctions [21]. This static checking will become simpler and more expressive

with C+ +20 constraints and concepts. 1) Consistency of smart pointers: Hedgehog manipulates

nodes by means of smart pointers based on an RAII (Resource Acquisition Is Initialization) technique, to avoid memory er-

rors in the library. Basically, a smart pointer is an object wrapping a pointer of a given type. In C + +, smart pointers

are modeled by a generic class, shared_ptr<T>, where T is the type of the wrapped pointer. To accept or reject a node, Hedgehog extracts the node’s

internal type from its smart pointer and checks this internal type’s inheritance. In Hedgehog, metafunctions have been designed to test the

compatibility of two smart pointers. 2) Node compatibility: Hedgehog checks compatibility rules when two nodes are linked by an edge in the graph:

1) If a node is set as the output of a graph, the node and the graph need to share the same output type, as shown in Figure 5a.

2) If a node is set as an input of a graph, the node and the graph need to share at least one input type, as shown in Figure 5b.

3) The output type of the source node must be one of the input types of the target node, as shown in Figure 5c.

Page 8:
Output Node I1 I1 Output Node X I1 I2 (a) Output Check Input Node I1 I2 I3 I1 I4 Input Node X I1 I2 I3 I4 I5 (b) Input Check Sender Receiver I1 I3 I2

I2 Sender X Receiver I1 I3 I2 I4 (c) Compatibility Check Figure 5: Compile-time check using metaprograming tech- niques

Listing 3 shows the compatibility test (3), using a static_assert to perform the test and produce a clear error message at compile-time.

static_assert( traits::Contains_v<Output, Inputs>, "The given io cannot be linked together" );

Listing 3: Metafunction invocation testing nodes compatibility V. R ESULTS The experiments conducted on Hedgehog help understand the

behavior of the library, and the impact that having an explicit representation has on performance.

In our experiments, there are two crucial parameters, the amount of data streaming through the graph (often determined

by decomposition parameters such as the block size in a matrix) and the number of threads for each Hedgehog node.

The amount of data streaming through the graph affects the degree of parallelism that can be achieved. Because Hedgehog

targets coarse-grain parallelism, it is important to determine an optimal decomposition size. For example, if the block size is

“too small”, then the underlying hardware may have poor uti- lization because each task does not execute enough instructions

compared to the system latency. If it is “too big”, then this will reduce the parallelism in Hedgehog because fewer pieces

of data feed the tasks. The number of threads for each task will also determine how many elements a task can process in

parallel. This can be detrimental if the processor gets oversub- scribed. The best methodology for approaching computation 1 2 4 8 16 32 0 1 2 4 6 8

10 Number of threads per task Latency (µs) 1 Input type 5 Input types 10 Input types HTGS Figure 6: Latency analysis for different task’s number of

threads in Hedgehog is setting good enough values for a ﬁrst run. This run is used to generate the DOT ﬁle feedback, which

identiﬁes bottlenecks, and helps determine better parameters to improve the performance for a speciﬁc architecture. These

graphs are portable, and only require parameter tuning for new architectures. This methodology justiﬁes experimentation

for performance , and was used to help identify the optimal parameters within our results. A. Data transfer latency

One of the major costs in our approach is the data transfer latency between tasks. Two parameters affect this latency:

(1) the number of threads per task, because all threads in a task group will share the same protected queues, which introduces

access contention, and (2) the number of input types, because a task will have one queue per input type.

Figure 6 shows the results of measuring the time to transfer one element between two tasks, averaged over one million

data transfers, on a computer with two Intel Xeon Silver 4114 CPU @ 2.20 GHz processors (10 physical cores, 20 logical

cores) and 192 GiB of memory. This latency varies between ≈ 1 µs to 10 µs. It grows with the number of threads in the

group of receiving tasks and the number of input types. These measurements are low enough that the data transfer costs can

be easily hidden by concurrently executing compute kernels. Furthermore, this latency is below that of HTGS for most common cases.

B. LU decomposition with partial pivoting One of our experiments was a CPU-based implementation of LU decomposition with partial pivoting [13].

The kernels used in our tasks are mainly composed of calls to the OpenBLAS [17] library in single-threaded mode. Our

Page 9:
256 512 1,024 2,048 4,096 100 120 140 160 180 Block Size Runtime (s) Hedgehog LAPACK Figure 7: LU with partial pivoting performance for a matrix

of 32768 × 32768 elements baseline was the LAPACK dgetrf routine, compiled with Open- BLAS in multi-threaded mode, used as a one-off call.

This methodology made it easier to reason about the complex dependencies and to instrument the code in a more sophis-

ticated way that allows the streaming of data in and out of the operation. The stream-based design provides partial fully

computed results before the computation completes. This is used to initiate the next step of a computation sooner.

To study end-to-end runtime performance, we ran 10 trials for the Hedgehog and LAPACK (Linear Algebra PACKage) imple-

mentations of LU decomposition with partial pivoting on two Intel Xeon E5-2680 v4 CPUs @2.40 GHz (28 physical cores,

56 logical cores) with 512 GiB of DDR4 memory. Figure 7 shows that Hedgehog obtains comparable overall performance

to the baseline. In this case, the optimal parameter happens to be a block size of 1024. Additionally, the streaming aspect

allows us to start getting partial results over 40 times faster than waiting for the entire matrix to ﬁnish computing. This has

potential for future research in understanding the intricacies of chaining streaming operations together by composing graphs

especially when it can be automated. C. Matrix multiplication Hedgehog is a library that allows computation in a hetero-

geneous node. We developed a BLAS-like GEneral Matrix Multiplication routine (GEMM) and ran it on a node with

two Intel Xeon Silver 4216 CPUs @2.1 GHz (16 physical cores, 32 logical cores) with 768 GiB DDR4 memory and four

Tesla V100-PCIe with 32 GiB HBM2 GPU, using 128k×128k single-precision matrices. As shown in Figure 8, the Hedge-

hog implementation is compared to the NVIDIA counterparts from their GPU-accelerated libraries for basic linear algebra,

cuBLASMg and cuBLAS-XT [5]. With an optimal block- 1 2 3 4 10 20 30 40 50 60 Number of GPUs TFLOPs Hedgehog cuBLAS-XT cuBLASMg Theoretical peak

Figure 8: Matrix multiplication on a matrix of 64k × 64k elements decomposed in 8k × 8k block elements

size the Hedgehog implementation achieves > 95% of the theoretical peak across 4 GPUs. This ﬁnal result required multiple iterations that were done

using Hedgehog’s experimentation for performance . This methodology starts with a simple CPU-only version which

is then augmented to use the GPU. The GPU version bun- dles the data transfers to and from the GPU and the actual

computation into its own graph. This was made possible by the composability of the Hedgehog graphs. The GPU graph is

further improved by inserting it into an ExecutionPipeline to scale the computation to multiple GPUs. These graphs could

be represented as a library, which would simplify the future development of Hedgehog-based applications.

The CPU and GPU versions reused the original representation of state. The primary focus between the versions was optimiz-

ing the transfer of data between the CPU and GPU as well as improving the data locality to avoid unnecessary copies. For

example, the memory manager was used to stay within the GPU memory limits, and cudaEvents were applied to memory

copy events to overlap data motion, computation, and all of the state management that is done within Hedgehog.

These experiments show that the overhead incurred by our approach is not detrimental to performance. It is also amenable

to using libraries that target ﬁne-grained parallelism, such as calls to cuBLAS to maximize performance. Lastly, the

explicit representation featured in Hedgehog is manageable. The LU decomposition with partial pivoting implementation

was completed in the course of one month by a non-domain specialist without any prior knowledge of the Hedgehog library

and the intricacies of parallel programming. This experience has continued to indicate to us that having a high-level

programming abstraction that can be reasoned about and that maps to execution is extremely valuable.

Page 10:
VI. C ONCLUSION In this paper, we have presented Hedgehog, a general-purpose library allowing developers to create a parallel computation

on a heterogeneous node. It differs from other approaches as it only uses its explicit data-ﬂow representation to implement

an algorithm, and relies on data-pipelining to get performance without a global scheduler. This approach operates entirely

based on the presence of data and achieves an overhead of ≈ 1 µs to 10 µs when transferring data between tasks in a graph.

Hedgehog supports a separation of concerns approach by providing several distinct components, such as computation,

localized state, memory management, and scaling through execution pipelines. The graph is constructed using these

components, and its representation is maintained throughout its execution. The developer can use this representation to

understand the processing. This helps developers to reason about complex operations at a higher level of abstraction.

This was demonstrated through the use of streaming data in and out of an operation to produce partial results as early

as possible. This was achieved by explicitly representing the localized states of the computation throughout the algorithm,

which aids with understanding when the results are ﬁnalized. In addition, Hedgehog can be easily extended as it relies on

class inheritance to create new types of tasks, as we have presented for CUDA-based tasks. Hedgehog operates effectively with heterogeneous computers

as well, which is validated by our achieved GPU utiliza- tion. This is feasible by making use of Hedgehog’s memory

management tools, to express memory locality and avoid unnecessary memory copies and keeps GPUs busy. VII. F UTURE WORK

Hedgehog has an explicit and static representation of the data- ﬂow graph. The graph structure is known at compile-time.

The latest C+ +standard (C+ +20) brings more tools to perform complex computation at compile-time, such as additions to

the constexpr speciﬁer. A compile-time tool will be developed to analyze a Hedgehog graph structure to identify design

mistakes such as data-races or cycles that cause deadlock. Another future work will be to extend Hedgehog to operate in

cluster environments. One approach is to build one Hedgehog graph per node with direct interaction with external cluster-

based communication tools and/or libraries. DISCLAIMER No approval or endorsement of any commercial product by the National

Institute of Standards and Technology is intended or implied. Certain commer-

cial software, products, and systems are identiﬁed in this report to facilitate

better understanding. Such identiﬁcation does not imply recommendations or endorsement by NIST, nor does it imply that the software and products

identiﬁed are necessarily the best available for the purpose. REFERENCES [1] C ´edric Augonnet et al. “StarPU: A Uniﬁed Platform for

Task Scheduling on Heterogeneous Multicore Architec- tures”. In: Concurr. Comput. : Pract. Exper. 23.2 (Feb.

2011), pp. 187–198. ISSN : 1532-0626. DOI : 10.1002/ cpe.1631. [2] Michael Bauer et al. “Legion: Expressing Locality and

Independence with Logical Regions”. In: Proceedings of the International Conference on High Performance

Computing, Networking, Storage and Analysis . SC ’12. Salt Lake City, Utah: IEEE Computer Society Press,

2012, 66:1–66:11. ISBN : 978-1-4673-0804-5. DOI : 10. 1109/SC.2012.71. [3] Timothy Blattner et al. “A hybrid task graph scheduler

for high performance image processing workﬂows”. In: Journal of signal processing systems 89.3 (2017), pp. 457–467. DOI : 10.1007/s11265-017-1262-6.

[4] H. Carter Edwards, Christian R. Trott, and Daniel Sunderland. “Kokkos”. In: J. Parallel Distrib. Comput.

74.12 (Dec. 2014), pp. 3202–3216. ISSN : 0743-7315. DOI : 10.1016/j.jpdc.2014.07.003. [5] Basic Linear Algebra on NVIDIA GPUs . https : / /

developer.nvidia.com/cublas. Last access: 2020-07-01. [6] I. Culjak et al. “A brief introduction to OpenCV”. In:

2012 Proceedings of the 35th International Convention MIPRO. 2012, pp. 1725–1730. [7] John Ellson et al. “Graphviz — open source graph

drawing tools”. In: Lecture Notes in Computer Science . Springer-Verlag, 2001, pp. 483–484. DOI : 10.1007/3- 540-45848-4 57.

[8] M. Frigo and S. G. Johnson. “The Design and Imple- mentation of FFTW3”. In: Proceedings of the IEEE

93.2 (2005), pp. 216–231. DOI : 10.1109/JPROC.2004. 840301. [9] Alexandre Bardakoff et al. Hedgehog Tutorials. Sept.

2020. URL : https://pages.nist.gov/hedgehog-Tutorials/. [10] J. A. Herdman et al. “Achieving Portability and Perfor-

mance through OpenACC”. In: 2014 First Workshop on Accelerator Programming using Directives . 2014, pp. 19–26. DOI : 10.1109/W ACCPD.2014.10.

[11] Hartmut Kaiser et al. STEllAR-GROUP/hpx: HPX V1.4.1: The C++ Standards Library for Parallelism and

Concurrency. Version 1.4.1. Feb. 2020. DOI : 10.5281/ zenodo.3675272. [12] Laxmitant V . Kal ´e et al. The CHARM Parallel Pro-

gramming Language and System: Part I – Descrip- tion of Language Features . Parallel Programming Lab-

oratory Technical Report 95-02. Last access: 2018- 01-02. Parallel Programming Laboratory Department

of Computer Science University of Illinois Urbana- Champaign, 1994. URL : http : / / charm . cs . uiuc . edu / papers/CharmSys1TPDS94.pdf.

[13] Gerson C. Kroiz et al. “Study of Exploiting Coarse- Grained Parallelism in Block-Oriented Numerical Lin-

ear Algebra Routines”. In: Proceedings of the 91st

Page 11:
Annual Meeting of the International Association of Ap- plied Mathematics and Mechanics . Submitted to https: //jahrestagung.gamm-ev.de/. 2020.

[14] Alexey Kukanov and Michael J. V oss. “The Founda- tions for Scalable Multicore Software in Intel Thread-

ing Building Blocks”. In: Intel Technology Journal 11 (2007). ISSN : 1535-864X. DOI : 10.1535/itj.1104.05.

[15] Qingyu Meng and Martin Berzins. “Uintah Hybrid Task-Based Parallelism Algorithm”. In: Proceedings of

SC12. IEEE, 2012. DOI : 10.1109/SC.Companion.2012. 237. [16] The OmpSs-2 Programming Model . https://pm.bsc.es/ ompss-2. Last access: 2018-08-16.

[17] Zhang Xianyi and Martin Kroeker. OpenBLAS: An optimized BLAS library . http://www.openblas.net/. Last access: 2020-05-22.

[18] OpenMP API Speciﬁcation: Version 5.0 November 2018. Sept. 2020. URL : https://www.openmp.org/spec- html/5.0/openmp.html.

[19] Jonathan Ragan-Kelley et al. “Halide: A Language and Compiler for Optimizing Parallelism, Locality, and

Recomputation in Image Processing Pipelines”. In: SIG- PLAN Not. 48.6 (June 2013), pp. 519–530. ISSN : 0362- 1340. DOI : 10.1145/2499370.2462176.

[20] Tutorial 1 - Simple Hadamard Product . https://pages. nist . gov / hedgehog - Tutorials / tutorials / tutorial1 . html. Last access: 2020-07-10.

[21] David Vandevoorde, Nicolai M. Josuttis, and Douglas Gregor. C++ Templates: The Complete Guide (2nd Edi-

tion). 2nd. Addison-Wesley Professional, 2017. ISBN : 0321714121. [22] Q. Wang et al. “AUGEM: Automatically generate high

performance Dense Linear Algebra kernels on x86 CPUs”. In: SC ’13: Proceedings of the International

Conference on High Performance Computing, Network- ing, Storage and Analysis . 2013, pp. 1–12. DOI : 10 . 1145/2503210.2503219.

Page 12:
Appendix: Artifact Description/Artifact Evaluation SUMMARY OF THE EXPERIMENTS REPORTED We have executed four experiments:

(1) Profiling on a MacBook Pro, 2015 (2) Latency test on a MacBook Pro, 2015 (3) Multi-GPUs matrix multiplication algorithm on a V100 server

(4) LU decomposition with partial pivoting on a BigTwin server Each of these experiments is presented in the paper. ARTIFACT AVAILABILITY

Software Artifact Availability: (One of these options remains.) —Some author-created software artifacts are NOT maintained

in a public repository or are NOT available under an OSI-approved license. Hardware Artifact Availability: (One of these options remains.)

—There are no author-created hardware artifacts. Data Artifact Availability: (One of these options remains.)

– There are no author-created data artifacts. Proprietary Artifacts: (One of these options remains.)

— None of the associated artifacts, author-created or otherwise, are proprietary. List of URLs and/or DOIs where artifacts are available:

(1) Matrix Multiplication: https://github.com/usnistgov/hedgehog- Tutorials/tree/V.1.0/advanced/tutorial1

(2) Profiling: https://github.com/usnistgov/hedgehog-Tutorials/ tree/V.1.0/tutorial1 CONSIDERATION FOR SCC: No. BASELINE EXPERIMENTAL SETUP, AND

MODIFICATIONS MADE FOR THE PAPER Relevant hardware details: (1) V100 server: Dual Intel(R) Xeon(R) Silver 4216 CPU @ 2.10GHz,

768 GB DDR4 RAM, Tesla PCIe V100 with 32 GB HBM2 (2) MacBook Pro, 2015: Intel(R) Core (TM) i7-4980HQ CPU @ 2.80GHz

(3) BigTwin server: Dual Intel(R) Xeon(R) E5-2680 v4 @ 2.40 GHz (56 logical cores) and 512 GB DDR4 RAM Operating systems and versions:

(1) V100 server: Ubuntu 18.04.4 LTS running Linux kernel 5.3.0 (2) MacBook Pro: macOS Catalina v.10.15.6

(3) BigTwin server: Ubuntu 18.04.4 LTS running Linux kernel 5.3.0 Compilers and versions: (1) V100 server: g++ 9 (2) MacBook Pro: g++ 10.2

(3) BigTwin server: g++8 Applications and versions: N/A Libraries and versions: (1) V100 server: OpenBLAS v0.3.6 / CUDA 10.2

(2) BigTwin server: OpenBLAS v0.3.6 Key algorithms: (1) V100 server: Matrix Multiplication (2) MacBook Pro: Profiling, Latency analysis

(3) BigTwin server: LU decomposition with partial pivoting Input datasets and versions: N/A Paper Modifications:

(1) Updated wording for GEMM, cuBLAS-XT, cuBLASMg, Graphviz (2) Updated references to use a single citation where we had multiple citations before

(3) Added code examples to present basic API calls (4) Change the color scheme for the code

(5) Added information about the graph composability and the execution pipeline (6) Rewrote State - State Manager relation

(7) Add a paragraph about condition_variable usage and data transfer via pointers (8) Add a link for the graphical representation

Output from scripts that gather execution environment informa- tion. V100 server: 1 SUDO_COMMAND=./collect_environment.sh 2 SHELL=/bin/bash

3 Distributor ID: Ubuntu 4 Description: Ubuntu 18.04.4 LTS 5 Release: 18.04 6 Codename: bionic 7 Linux 5.3.0-51-generic #44~18.04.2-Ubuntu SMP Thu

Apr 23 14:27:18 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux ↩→ ↩→ 8 9 Architecture: x86_64 10 CPU op-mode(s): 32-bit, 64-bit 11 Byte Order: Little Endian

12 CPU(s): 64 13 On-line CPU(s) list: 0-63 14 Thread(s) per core: 2 15 Core(s) per socket: 16 16 Socket(s): 2 17 NUMA node(s): 2

18 Vendor ID: GenuineIntel 19 CPU family: 6 20 Model: 85 21 Model name: Intel(R) Xeon(R) Silver 4216 CPU @ 2.10GHz↩→ 22 Stepping: 7

Page 13:
23 CPU MHz: 800.068 24 CPU max MHz: 3200.0000 25 CPU min MHz: 800.0000 26 BogoMIPS: 4200.00 27 Virtualization: VT-x 28 L1d cache: 32K

29 L1i cache: 32K 30 L2 cache: 1024K 31 L3 cache: 22528K 32 NUMA node0 CPU(s): 0-15,32-47 33 NUMA node1 CPU(s): 16-31,48-63 34

35 Flags: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx

pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor

ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand

lahf_lm abm 3dnowprefetch cpuid_fault epb cat_l3 cdp_l3 invpcid_single intel_ppin ssbd mba ibrs ibpb stibp ibrs_enhanced tpr_shadow vnmi

flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid cqm mpx rdt_a avx512f avx512dq rdseed adx smap clflushopt clwb

intel_pt avx512cd avx512bw avx512vl xsaveopt xsavec xgetbv1 xsaves cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln

pts pku ospke avx512_vnni md_clear flush_l1d arch_capabilities ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ 36 MemTotal: 1055473624 kB

37 MemFree: 1051503124 kB 38 MemAvailable: 1049176588 kB 39 Tue Sep 8 14:35:00 2020 40 +----------------------------------------------------+

41 | NVIDIA-SMI 440.64.00 Driver Version: 440.64.00 CUDA Version: 10.2 |↩→ 42 |-------------------------------+--------------------+

43 | GPU Name Persistence-M| Bus-Id Disp.A | Volatile Uncorr. ECC |↩→ 44 | Fan Temp Perf Pwr:Usage/Cap| Memory-Usage | GPU-Util Compute M. |↩→

45 |===============================+====================| 46 47 | 0 Tesla V100-PCIE... On | 00000000:3B:00.0 Off | 0 |↩→

48 | N/A 37C P0 27W / 250W | 0MiB / 32510MiB | 0% Default |↩→ 49 +-------------------------------+--------------------+

50 | 1 Tesla V100-PCIE... On | 00000000:60:00.0 Off | 0 |↩→ 51 | N/A 31C P0 27W / 250W | 0MiB / 32510MiB | 0% Default |↩→

52 +-------------------------------+--------------------+ 53 | 2 Tesla V100-PCIE... On | 00000000:61:00.0 Off | 0 |↩→

54 | N/A 32C P0 25W / 250W | 0MiB / 32510MiB | 0% Default |↩→ 55 +-------------------------------+--------------------+

56 | 3 Tesla V100-PCIE... On | 00000000:86:00.0 Off | 0 |↩→ 57 | N/A 40C P0 28W / 250W | 0MiB / 32510MiB | 0% Default |↩→

58 +-------------------------------+--------------------+ BigTwin server: 1 USER=USER 2 LOGNAME=USER 3 TERM=xterm 4 USERNAME=USER

5 PATH=/usr/local/sbin:/usr/local/bin: 6 /usr/sbin:/usr/bin:/sbin:/bin:/snap/bin 7 LANG=en_US.UTF-8 8 SUDO_COMMAND=./collect_environment.sh

9 SHELL=/bin/bash 10 Distributor ID: Ubuntu 11 Description: Ubuntu 18.04.5 LTS 12 Release: 18.04 13 Codename: bionic 14 + uname -a

15 Linux 5.4.0-42-generic #46~18.04.1-Ubuntu SMP Fri Jul 10 07:21:24 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux ↩→ ↩→ 16 + lscpu 17

18 Architecture: x86_64 19 CPU op-mode(s): 32-bit, 64-bit 20 Byte Order: Little Endian 21 CPU(s): 56 22 On-line CPU(s) list: 0-55

23 Thread(s) per core: 2 24 Core(s) per socket: 14 25 Socket(s): 2 26 NUMA node(s): 2 27 Vendor ID: GenuineIntel 28 CPU family: 6 29 Model: 79

30 Model name: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz↩→ 31 Stepping: 1 32 CPU MHz: 1200.432 33 CPU max MHz: 3300.0000 34 CPU min MHz: 1200.0000

35 BogoMIPS: 4800.49 36 Virtualization: VT-x 37 L1d cache: 32K 38 L1i cache: 32K 39 L2 cache: 256K 40 L3 cache: 35840K

41 NUMA node0 CPU(s): 0-13,28-41

Page 14:
Appendix: Artifact Description/Artifact Evaluation 42 NUMA node1 CPU(s): 14-27,42-55 43 44 Flags: fpu vme de pse tsc msr pae mce

cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs

bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid

dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb cat_l3

cdp_l3 invpcid_single pti intel_ppin ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 hle avx2 smep

bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap intel_pt xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln

pts md_clear flush_l1d ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ ↩→ 45 + cat /proc/meminfo 46 MemTotal: 528263716 kB 47 MemFree: 433407420 kB

48 MemAvailable: 502555512 ARTIFACT EVALUATION Verification and validation studies: •Matrix Multiplication

– The matrix multiplication experiment ran 20 times to com- pute the average and standard deviation

– The accuracy of the output was tested such as the dif- ference of our matrix output and a matrix ground truth

(Single OpenBLAS call) is not greater than 3×the machine epsilon for the floating point representation

(https://en.cppreference.com/w/cpp/types/numeric_limits/ epsilon). •Profiling – The Hadamard product ran 1000 times with and without

profiling (2000 runs totals). We performed a statistical analysis that is presented in the paper. •Latency

– The latency experiment ran 20 times to get the average and standard deviation. Accuracy and precision of timings: We have exclusive access to

all of the hardware, and no other users were able to execute while we were performing timing analysis. We have used the standard

timer std::system_clock to instrument our algorithms. Quantified the sensitivity of results to initial conditions and/or

parameters of the computational environment: When possible, we compute the standard deviations for all of our experiments and

report them within the paper. Controls, statistics, or other steps taken to make the measurements

and analyses robust to variability and unknowns in the system. In order to validate our matrix multiplication computation with Hedge-

hog, we estimated the accuracy of our results. The matrix multipli- cation computation is defined as, 𝐶 = 𝐴·𝐵+𝐶 with: •𝐴: a 𝑛·𝑚matrix,

•𝐵: a 𝑚·𝑝 matrix, •𝐶: a 𝑛·𝑝 matrix. The values of 𝐴, 𝐵, and 𝐶 are real random values taken between

[0,1). Because we are using limited size floating point numbers, the matrices are defined as: 𝐴= 𝑎𝑖 𝑗+𝛼𝑖 𝑗 

{𝑖 ∈N|0 ≤𝑖 < 𝑛}{𝑗 ∈N|0 ≤𝑗 < 𝑚}{𝛼 ∈R|𝛼 ≪0} 𝐵 = 𝑏𝑗𝑘 +𝛽𝑗𝑘  {𝑗 ∈N|0 ≤𝑗 < 𝑚}{𝑘 ∈N|0 ≤𝑘 < 𝑝}{𝛽 ∈R|𝛼 ≪0} 𝐶 = 𝑐𝑖𝑘 +𝛾𝑖𝑘 

{𝑖 ∈N|0 ≤𝑖 < 𝑛}{𝑘 ∈N|0 ≤𝑘 < 𝑝}{𝛾 ∈R|𝛼 ≪0} 𝛼, 𝛽, 𝛾 model the errors due to the finite representation of real

values. The representation is the same in a given machine. As such, these errors have the same upper bound with a value 𝜖. We will therefore use:

∀𝑖,∀𝑗,∀𝑘, 𝛼𝑖 𝑗 = 𝛽𝑗𝑘 = |𝛾𝑖𝑘 |= 𝜖. This yields the following expansion for a row-column multipli- cation: ∀𝑖,∀𝑘,(𝐴·𝐵)𝑖 𝑗= Õ 𝑗 (𝑎𝑖 𝑗+𝜖)·( 𝑏𝑗𝑘 +𝜖) = Õ 𝑗

𝑎𝑖 𝑗·𝑏𝑗𝑘 +𝜖·(𝑎𝑖 𝑗+𝑏𝑗𝑘 ) We drop𝜖2 in the expansion above because 𝜖 is defined as the

representation limit and we know that 𝜖2 cannot be represented as: 0 < 𝜖 << 1 0 < 𝜖2 << 𝜖 One element in the result matrix becomes:

∀𝑖,∀𝑘,(𝐴·𝐵+𝐶)𝑖𝑘 = 𝑐𝑖𝑘 +𝜖+ Õ 𝑗 𝑎𝑖 𝑗·𝑏𝑗𝑘 +𝜖·(𝑎𝑖 𝑗+𝑏𝑗𝑘 ) = Õ 𝑗 𝑎𝑖 𝑗·𝑏𝑗𝑘 +𝑐𝑖𝑘 + Õ 𝑗 𝜖·(𝑎𝑖 𝑗+𝑏𝑗𝑘 )+𝜖

Let us define the 𝑛·𝑝 matrix 𝑅, which is the true result of the matrix multiplication 𝐴·𝐵+𝐶 as: ∀𝑖,∀𝑘,𝑅𝑖𝑘 = Õ 𝑗 𝑎𝑖 𝑗·𝑏𝑗𝑘 +𝑐𝑖𝑘

We have the following results with our finite representation of floating point numbers: ∀𝑖,∀𝑘,(𝐴·𝐵+𝐶)𝑖𝑘 = 𝑅𝑖𝑘 +𝜖·(1 + Õ 𝑗 (𝑎𝑖 𝑗+𝑏𝑗𝑘 )) (1)

To compute the accuracy of our algorithm, we first perform the matrix multiplication computation with a given library (Open-

BLAS), which gives the result 𝑇. We then use our library to carry out the computation to obtain result 𝑀. With a perfect represen-

tation of numbers 𝑇 −𝑀 = 0. Because of Equation 1, 𝑇 and 𝑀 are affected by the same representation problem, so the same error applies:

Page 15:
∀𝑖,∀𝑘,𝑇𝑖𝑘 = 𝑅𝑇 𝑖𝑘 +𝜖𝑇 ·(1 + Õ 𝑗 (𝑎𝑇 𝑖 𝑗+𝑏𝑇 𝑗𝑘 )) ∀𝑖,∀𝑘,𝑀𝑖𝑘 = 𝑅𝑀 𝑖𝑘 +𝜖𝑀 ·(1 + Õ 𝑗 (𝑎𝑀 𝑖 𝑗+𝑏𝑀 𝑗𝑘 )) The threshold used to test our accuracy is:

∀𝑖,∀𝑗,∀𝑘, 𝑇𝑖 𝑗−𝑀𝑖 𝑗  =  𝑅𝑇 𝑖𝑘 +𝜖𝑇 ·(1 + Õ 𝑗 (𝑎𝑇 𝑖 𝑗+𝑏𝑇 𝑗𝑘 )) −(𝑅𝑀 𝑖𝑘 +𝜖𝑀 ·(1 + Õ 𝑗 (𝑎𝑀 𝑖 𝑗+𝑏𝑀 𝑗𝑘 )))  However, ∀𝑖,∀𝑗,∀𝑘,𝑎𝑀 𝑖 𝑗 = 𝑎𝑇 𝑖 𝑗,𝑏𝑀 𝑗𝑘 = 𝑏𝑇

𝑗𝑘 ,𝑐𝑀 𝑖𝑘 = 𝑐𝑇 𝑖𝑘 So, 𝑅𝑇 = 𝑅𝑀 Õ 𝑗 (𝑎𝑇 𝑖 𝑗+𝑏𝑇 𝑗𝑘 )= Õ 𝑗 (𝑎𝑀 𝑖 𝑗+𝑏𝑀 𝑗𝑘 )= 𝑆𝑖𝑘 We also consider that𝜖𝑇 = −𝜖𝑀 represents the worst-case scenario

with no error compensation. We have: |𝑇𝑖𝑘 −𝑀𝑖𝑘 |= |2 ·𝜖·(1 +𝑆𝑖𝑘 )| Taking the absolute value will add an𝜖, and |𝑆𝑖𝑘 |= 𝑆𝑖𝑘 because the

values of 𝐴, 𝐵, and 𝐶 are real random values taken between [0,1). Finally we have: ∀𝑖,∀𝑘,𝐸𝑟𝑟𝑜𝑟 𝑖𝑘 = 2 ·𝜖·(1 +𝑆𝑖𝑘 )+𝜖 (2)

We can have a lower bound as: ∀𝑖,∀𝑘,𝐴𝑝𝑝𝑟𝑜𝑥𝑖𝑚𝑎𝑡𝑒𝐸𝑟𝑟𝑜𝑟 𝑖𝑘 = 3 ·𝜖 (3) Equations 2 and 3 allow us to conclude that the results of Open-

BLAS and Hedgehog’s matrix multiplications are within 3 ·𝜖.


</paper1>

</PAPERS>



<WEBSITES>

<Website1>

<link1>
Tutorial 4 - Matrix Multiplication with cycle | Hedgehog Tutorials                      Hedgehog Tutorials

AboutPreambleTutorial 1 - Simple Hadamard ProductTutorial 2 - Hadamard Product with Managed StateTutorial 3 - Parallel ReductionTutorial 4 - Matrix Multiplication with cycleTutorial 5 - Matrix Multiplication on NVIDIA GPU with memory managementTutorial 6 - Matrix Multiplication on multiple NVIDIA GPUsTutorial 7 - Compile-time analysisTutorial 8 - Extensibility in HedgehogProfiling toolsMoving from Hedgehog v.2 to Hedgehog v.3

Tutorial 4 - Matrix Multiplication with cycle   Content  Goal Computation Data structure Task State and State Manager Graph Conclusion   Goal

This tutorial aims to create a BLAS-like Matrix Multiplication routine (C += A * B) to introduce how to resolve cycles in a Hedgehog graph.

Hedgehog graphs are allowed to have cycles.

The problem is, whilst they are authorized, they need to be taken care of because if no extra care is used by a developer, the cyclic graphs will deadlock.

This is because by default, a node in Hedgehog can terminate if 1) there is no antecedent nodes (node connected and sending data to the node) alive and 2) there is no data in the input queues.

When a cycle is built, the first condition is never met and the node never terminates. Therefore, the graph deadlocks.

That is why we need to resolve cycles in the graph. This can be done by customizing the definition of the canTerminate function for one of the tasks in a cycle.

In this tutorial, the OpenBLAS library is required to do the computation.  Computation

The computation is a BLAS-like Matrix Multiplication routine (C += A * B) with:  A, a (n * m) random matrix, B, a (m * p) random matrix,

C, a (n * p) random matrix.  The computation steps are:  A traversal of matrices A, B, and C that produces blocks,

The creation of compatible pairs of blocks from A and B, A partial matrix multiplication on the pair of blocks producing a new âtemporary blockâ,

The accumulation into the C blocks of the compatible temporary blocks, Serve the output block when it is ready.

Points 1, 3 and 4 will be represented as tasks.

Points 2 and 5 will be represented as states and state managers, because it represents points where data needs to be gathered or stored temporally to satisfy dependencies.

To create an output block it needs a full row of blocks from matrix A and a full column of blocks from matrix B, so two tasks will be implemented to traverse the matrices properly, as shown in the figure below.

Data structure The same data structure representing the matrix and the matrix blocks are reused from tutorial 1 and tutorial 2.

The triplets are not used because we do not need to carry a block of A, B, and C, just a pair is used for the product.

A special matrix block specialization with id as âpâ is used for the temporary blocks (partial results).  Computation task

Here the tasks are simple:  The product task is a call to the sgemm (single precision) or dgemm (double precision) routine from OpenBLAS,

the addiction task, the sum of two contiguous pieces of memory.   State and State Manager States

Multiples âstatesâ are defined in this algorithm:

âInputBlockStateâ: The state is used to create a pair of compatible blocks from matrices A and B. Because each of the blocks are used multiple time, these blocks maintain a âtime to leaveâ, which is defined at state construction. When the time to leave reaches 0, then the block is discarded from the temporary storage.

âPartialComputationStateâ: The state creates a pair of blocks from a compatible temporary block and block from matrix C.   State Manager

We could have only used the default state manager for these states if there were no cycles in the graph.

But because of the cycle between the addition task and the partial computation state, a special state manager has to be defined from the âStateManagerâ, and the âcanTerminateâ method has to be overloaded to resolve the cycle.

template<class Type, Order Ord = Order::Row> class PartialComputationStateManager : public hh::StateManager< 2,

MatrixBlockData<Type, 'c', Ord>, MatrixBlockData<Type, 'p', Ord>,

std::pair<std::shared_ptr<MatrixBlockData<Type, 'c', Ord>>, std::shared_ptr<MatrixBlockData<Type, 'p', Ord>>>, MatrixBlockData<Type, 'c', Ord> > {

public: explicit PartialComputationStateManager(std::shared_ptr<PartialComputationState<Type, Ord>> const &state) : hh::StateManager< 2,

MatrixBlockData<Type, 'c', Ord>, MatrixBlockData<Type, 'p', Ord>,

std::pair<std::shared_ptr<MatrixBlockData<Type, 'c', Ord>>, std::shared_ptr<MatrixBlockData<Type, 'p', Ord>>>, MatrixBlockData<Type, 'c', Ord>

>(state, "Partial Computation State Manager", false) {}  [[nodiscard]] bool canTerminate() const override { this->state()->lock();

auto ret = std::dynamic_pointer_cast<PartialComputationState<Type, Ord>>(this->state())->isDone(); this->state()->unlock(); return ret; } };

template<class Type, Order Ord = Order::Row> class PartialComputationState : public hh::AbstractState< 2,

MatrixBlockData<Type, 'c', Ord>, MatrixBlockData<Type, 'p', Ord>,

std::pair<std::shared_ptr<MatrixBlockData<Type, 'c', Ord>>, std::shared_ptr<MatrixBlockData<Type, 'p', Ord>>>, MatrixBlockData<Type, 'c', Ord> > {

//[...] bool isDone() { return ttl_ == 0; }; //[...] };

The canTerminate method overrides the default conditions to terminate the node: 1) there is no antecedent nodes (node connected and sending data to the node) alive and 2) there is no data in the input queues.

Now, the state managers terminate when the method isDone from the state it manages returns true, which corresponds to the end of the state computation.

We can note that this state / state manager have 2 output types.

When a pair is produced it is sent to the Addition Task for accumulation, and when a C block alone is produced it is sent as output of the graph. The C block is only outputted when it has been fully computed.

Graph Hedgehog presents and uses a directed graph. Which means, that cycles are possible and without special care will end in deadlock.

This is because a node, by default, will terminate if these two conditions are true:

1: Are there no âinput nodesâ (nodes that send data to the considered nodes) alive ? 2: Are all the input data queues empty ?

Because of the cycle, itâs possible there is no data in the input queues, but for each of them one of their âinput nodesâ may be alive.

To break the cycle, knowledge specific to the computation is needed to know when itâs done, and this test is represented by overloading the âcanTerminateâ method.

Here is the final graph:  To deal with the multiple outputs of the PartialComputationState state, we have constructed the graph as follows:

matrixMultiplicationGraph.edges(stateManagerPartialComputation, additionTask); matrixMultiplicationGraph.outputs(stateManagerPartialComputation);

It reads, construct an edge between all valid common types between the stateManagerPartialComputation and additionTask nodes, and set the stateManagerPartialComputation node as output of the graph for all common types.

In this case there is only one type between the stateManagerPartialComputation and the additionTask nodes (std::pair<std::shared_ptr<MatrixBlockData<MatrixType, âaâ, OrdÂ», std::shared_ptr<MatrixBlockData<MatrixType, âbâ, OrdÂ»>) and there is only one type that can be used to produce output of the graph (MatrixBlockData<MatrixType, âcâ, Ord>).

We could have written the graph construction as:

matrixMultiplicationGraph.edge<std::pair<std::shared_ptr<MatrixBlockData<MatrixType, 'a', Ord>>, std::shared_ptr<MatrixBlockData<MatrixType, 'b', Ord>>>>(stateManagerPartialComputation, additionTask);

matrixMultiplicationGraph.output<MatrixBlockData<MatrixType, 'c', Ord>>(stateManagerPartialComputation);

These API are useful if you want to make only specific connections between nodes even though they could have others.  Conclusion

We have seen in this tutorial:  How to manage a cycle in a graph, How to use multiple output types in a node.          Hedgehog Tutorials

Tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

</link1>

<link2>
About | Hedgehog Tutorials                      Hedgehog Tutorials

AboutPreambleTutorial 1 - Simple Hadamard ProductTutorial 2 - Hadamard Product with Managed StateTutorial 3 - Parallel ReductionTutorial 4 - Matrix Multiplication with cycleTutorial 5 - Matrix Multiplication on NVIDIA GPU with memory managementTutorial 6 - Matrix Multiplication on multiple NVIDIA GPUsTutorial 7 - Compile-time analysisTutorial 8 - Extensibility in HedgehogProfiling toolsMoving from Hedgehog v.2 to Hedgehog v.3

About

This is the git repository presenting the tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

Credits Alexandre Bardakoff Timothy Blattner Walid Keyrouz Bruno Bachelet LoÃ¯c Yon Mary Brady Contact us

Timothy Blattner (timothy.blattner ( at ) nist.gov) Disclaimer

NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the software in any medium, provided that you keep intact this entire notice. You may improve, modify and create derivative works of the software or any portion of the software, and you may copy and distribute such modifications or works. Modified works should carry a notice stating that you changed the software and should note the date and nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the source of the software.

NIST-developed software is expressly provided âAS IS.â NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE.

You are solely responsible for determining the appropriateness of using and distributing the software and you assume all risks associated with its use, including but not limited to the risks and costs of program errors, compliance with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of operation. This software is not intended to be used in any situation where a failure could cause risk of injury or damage to property. The software developed by NIST employees is not subject to copyright protection within the United States.

Hedgehog Tutorials

Tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

</link2>

<link3>
Profiling tools | Hedgehog Tutorials                      Hedgehog Tutorials

AboutPreambleTutorial 1 - Simple Hadamard ProductTutorial 2 - Hadamard Product with Managed StateTutorial 3 - Parallel ReductionTutorial 4 - Matrix Multiplication with cycleTutorial 5 - Matrix Multiplication on NVIDIA GPU with memory managementTutorial 6 - Matrix Multiplication on multiple NVIDIA GPUsTutorial 7 - Compile-time analysisTutorial 8 - Extensibility in HedgehogProfiling toolsMoving from Hedgehog v.2 to Hedgehog v.3

Profiling tools   In order to get performance, it is important to understand how the graph behaves.

One of the main focuses in Hedgehog is to be as explicit as possible following âwhat is designed is what is executedâ.

However, it is not enough to get the best performance on a specific system.

We have developed and added to the main library profiling mechanisms to help understand underlying problems on the design and bottlenecks.

There are components:  Dot file generation, The signal handler, A compatibility with NVIDIA NVTX.   Dot file generation API

The dot file generator uses a visitor pattern that visits a graph and its nodes, gathering metrics and serving them under the dot format (https://graphviz.org/doc/info/lang.html).

The dot generator colors nodes based on the specified color scheme (none, execution time, or wait time). This is useful to analyze the state of the computation and help pinpoint bottlenecks during the execution of the Hedgehog graph.

Each of the tutorials presents the dot representation of the graph used in the tutorial. It is invoked through the graph method: void createDotFile(

std::filesystem::path const &dotFilePath, // Path to the file to create ColorScheme colorScheme = ColorScheme::NONE, // Color scheme selection

StructureOptions structureOptions = StructureOptions::NONE, // Graph structure option

InputOptions inputOption = InputOptions::GATHERED, // Input presentation option DebugOptions debugOption = DebugOptions::NONE, // Debug option

std::unique_ptr<ColorPicker> colorPicker = std::make_unique<JetColor>(), // Color picker bool verbose = false // Verbose flag );  Options

Here are the function parameters and their options:  dotFilePath: Path to the file to generate, if the file already exists it will be replaced.

colorScheme: Node color scheme used to generate the graph. It could be:  hh::ColorScheme::NONE: Default presentation, no coloration added,

hh::ColorScheme::EXECUTION: The nodes are colored depending on the execution (processing) time,

hh::ColorScheme::WAIT: The nodes are colored depending on the wait (idle) time.

structureOptions: Way to group nodes (some node can be duplicated as the hh::AbstractTask) and how the edges are presented. It could be:

hh::StructureOptions::NONE: Default presentation, the groups are presented with one node and no extra information is added to the edge.

hh::StructureOptions::THREADING: Present all the nodes in a group with different nodes.

hh::StructureOptions::QUEUE: Present extra information on the queue (number of elements in the queue / maximum queue size during the execution).

hh::StructureOptions::ALL: Combination of hh::StructureOptions::THREADING and hh::StructureOptions::QUEUE.

Input options: Shows if the metrics are presented per input type or with all the input types gathered

hh::InputOptions::GATHERED: Present the execution time for all input type gathered hh::InputOptions::SEPARATED: Shows the time per input type

debugOption: Add information for debugging purpose. It could be:  hh::DebugOptions::NONE: Default presentation, no extra information added.

hh::DebugOptions::ALL: Shows debug information such as pointer addresses for nodes and edges.

colorPicker: Choose the colors used to color the nodes. It could be anything inheriting from the ColorPicker abstraction, we have embedded:

JetColor: Default color picker, following the Jet scheme.

BlueToRed: Gradient from pure blue to pure red, blue being the lowest value and red the highest.

verbose: Flag for verbose mode, if true, a message is shown if the file is created or replaced.

The edges by default present an edge for each type connecting inputs/outputs of nodes.

If the option hh::StructureOptions::QUEUE or hh::StructureOptions::ALL is used, the current number of elements in the queue for this type waiting to be processed is showed alongside the maximum queue size during the whole execution.

Metrics The metrics gathered are:  Edge:

[hh::StructureOptions::QUEUE or hh::StructureOptions::ALL]: queue size and maximum queue size during the execution.   (Outer/Main) Graph:

Total graph execution duration Creation duration   Task / State Manager:  [hh::DebugOptions::ALL]: Number of predecessor nodes connected

[hh::DebugOptions::ALL]: Is thread active [hh::DebugOptions::ALL]: Number of active threads in the group Number elements received

Wait duration (thread idle time) Dequeue + execution duration Execution duration per element

[If memory manager attached]: Wait duration to acquire memory from the memory manager

All the durations are gathered in nanoseconds with a std::chrono::system_clock and presented with the most significant unit (s, ms, us, or ns). Cost

In paper DOI: 10.1109/PAWATM51920.2020.00006, we have presented a study about the cost of using this tool.

We have discovered that there is no statistical difference in average between the end-to-end executions duration with and without using this tool.

Therefore, we always advise users to use this tool to get a profile on every execution because 1) it is âcostlessâ in terms of execution duration and 2) it helps to understand the execution and improve it.

Few examples Here are few examples of dot graph generations. Color schemes

The following presents the graph of Tutorial 4 with different color schemes:

It presents the three options available on Hedgehog, in order from left to right: coloration depending on the waiting time (idle thread), no coloration, and coloration depending on the execution time.

Threading options The following presents how a node with multiple threads can be presented (here the ProductTask):

On top, the ProductTask three threads are presented with a single node.

Its metrics (number of elements received, wait time, dequeue + execution time, and the execution time per element) are served with statistics (minimum value, average +- stdev, and maximum value).

On bottom, each thread is presented with different nodes. The timings for each thread are exactly how the thread was executed within Hedgehog.

Queue options The following presents the different queue options.  By default, on top, only the type flowing through an edge is presented.

When the option StructureOptions::QUEUE or StructureOptions::ALL is used, the current Queue Size (here QS=0), and the Maximum Queue Size during the whole execution (here MQS=3). If the QS is greater than 0, then that means there was data within its queue waiting to be processed when the dot file was generated. Sometimes this can be used to pinpoint issues in the design of a graph, particularly when used in conjunction with the signal handler on a deadlocked graph.

How to use it ? Analyzing the dot graph presentation provides a variety of insights into how the execution was done within Hedgehog.

During development, usually it is known which task contains the most complexity and should consume the most execution time. This knowledge can come in handy when visualizing the graph. For instance, when coloring the graph based on execution time, if the most compute intensive task is not highlighting as red, then there is additional overhead being experienced within the graph. This is often a good starting point.

The next piece of the dot graph that is often analyzed is the queue structure. The MQS (Max Queue Size) is extremely useful to identify tasks that have a lot of data waiting to be processed. This could be a result of insufficient parallelism when processing that data or that the source of the data is producing at a much higher rate than what the task is able to process. The MQS is often useful to identify areas of parallelism in the graph and where other tasks are being over utilized. For example, if the MQS is 1, then most likely there is little parallelism available for that task as there is insufficient data flowing. So having more than 1 thread in this case may or may not be of benefit in that implementation. However it could also help indicate areas where optimizations can be applied, such as changing the decomposition strategy to improve the amount of data flowing into that task, so that parallelism can be used to process each element.

Combining both the execution time analysis and MQS analysis can help identify a variety of behaviors when the graph was executed; such as, data stalling, nodes lacking parallism, too complex nodes, or too big data. Once pinpointed, you can experiment with the graph by altering various thread configurations for nodes or adjusting data decomposition. For example, if there is a lot of data waiting to be processed (identified by the maximum queue size), then increasing the number of threads attached to that node or improving the throughput within the execute for that node will help with keeping up with the rate that data is being sent. Lastly, if the problem is due to Hedgehog latency (too small data), then it may be worth changing the coarseness of the pieces of data.

The queue size (QS) can also be important to analyze, particularly when debugging a deadlocked graph.

In general, a queue size non equal to zero is a problem. It could indicate that some input data has not been processed.

So, either it is wanted because the canTerminate method has been designed as such, or the QS can help pinpoint problem node[s] that may be the origin of a deadlock. A deadlocked graph can be visualized by using Hedgehogâs signal handler integration as described in the next section.

The ways to intrepret the dot file depends a lot on how the algorithm operates. To facilitate additional insights into how a node in Hedgehog performs, we have added the extraPrintingInformation function. Overriding this function into a task adds the output onto the node in the dot file. Here are some usage examples: (1) Output the data transfer throughput when copying data to/from the GPU, (2) Output the read throughput from disk, or (3) splitting up the computation within a task and timing each component. These are just a few examples of the types of insights that can be used to provide additional metrics to help pinpoint areas of improvement in the design and implementation of a Hedgehog graph.

Signal Handler One of the most difficult problems that can occur when using Hedgehog and parallel algorithms in general are deadlocks.

While we canât prevent it from happening, we have added the ablity to visualize the graph when it has entered into a deadlock state. This is achieved by attaching the Hedgehog signal handler to your graph.

The main idea of this tool is to react when an OS signal is sent to the program (SIGTERM or SIGKILL for example) and create a dot file of the graph.

#include "hedgehog/hedgehog.h"  // Simple task doing nothing class TaskIntInt : public hh::AbstractTask<1, int, int>{

void execute(std::shared_ptr<int> ptr) override { this->addResult(ptr); } };   int main() { // Graph's creation hh::Graph<1, int, int> g;

auto t = std::make_shared<TaskIntInt>();  g.inputs(t); g.outputs(t);  // Register the graph to the GraphSignalHandler

hh::GraphSignalHandler<1, int, int>::registerGraph(&g);  // Register the signals hh::GraphSignalHandler<1, int, int>::registerSignal(SIGABRT);

hh::GraphSignalHandler<1, int, int>::registerSignal(SIGKILL); hh::GraphSignalHandler<1, int, int>::registerSignal(SIGTERM);  // Execute the graph

g.executeGraph();  for(int i = 0; i < 1000000000; ++i){ g.pushData(std::make_shared<int>(i)); }  g.finishPushingData();  g.waitForTermination(); }

So if the graph is deadlocked, and you have attached the SIGTERM or SIGKILL signals to your graph, then when the program is terminated or killed then the graph at that point in time is outputted as a dot file.

For example, here is the graph when signal 15 is sent (SIGTERM) for the previous example graph:

One common source of deadlock is also related to incorrect usage when executing the graph and then forgetting to mark that the graph has finished pushing data. So try to follow the structure: (1) executeGraph, (2) finishPushingData, and (3) waitForTermination. This will ensure that at minimum the graph will correctly send appropriate terminations to the inputs of the graph. If the graph deadlocks beyond this case, then there could be incorrectly handled cycles or other conditions that prevent a task from checking canTerminate.

NVIDIA NVTX The last tool included in Hedgehog is an interface to the NVTX tool from NVIDIA.

The NVTX library allows us to annotate events in the code (different states of the nodes in the graph), and presents them in a visualization with the NVIDIA Nsight VSE tool.

If NVTX is available in your system, and activated in the CMAKE (ENABLE_NVTX option) the events collection will be activated.

Once activated, the executable can be invoked through the NVIDIA Nsight VSE tool and the following graph can be presented:

On the left the different nodesâ name are presented, and for each of the nodes the different events are presented in a timely fashion.

In red are the waiting (idle) thread events, in green are the processing events, and in yellow are the wait for memory from a memory manager events. Hovering over the red events provides an additional payload variable, which indicates the queue size at that point in time.

Hedgehog Tutorials

Tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

</link3>

<link4>


Hedgehog Tutorials | Tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

Hedgehog Tutorials

AboutPreambleTutorial 1 - Simple Hadamard ProductTutorial 2 - Hadamard Product with Managed StateTutorial 3 - Parallel ReductionTutorial 4 - Matrix Multiplication with cycleTutorial 5 - Matrix Multiplication on NVIDIA GPU with memory managementTutorial 6 - Matrix Multiplication on multiple NVIDIA GPUsTutorial 7 - Compile-time analysisTutorial 8 - Extensibility in HedgehogProfiling toolsMoving from Hedgehog v.2 to Hedgehog v.3

In this repository we present the tutorials for the Hedgehog API. The source code for the tutorials can be found Here. Content  Dependencies

Getting started Tutorial contents Credits Contact Us Disclaimer  Dependencies

All tutorials depend on the Hedgehog library, location is specified using:  cmake -DHedgehog_INCLUDE_DIR=<dir>  Tutorial 4 requires OpenBLAS

Tutorial 5 and 6 require CUDA .  TCLAP is used and is embedded in the repository to parse the command of the different tutorials. Getting started

The tutorials presented here need to be compiled with a C++ compiler that is compatible with C++20 and has the standard filesystem library accessible.

Tested Compilers:  g++ 11.1+ clang 10 MSVC 14.33

For the static analysis (hh_cx) a compiler with the constexpr std::vector (P1004R2) and constexpr std::string (P0980R1) is needed, tested with gcc 12.1.0+.

To use the Hedgehog API include the following header file: #include <hedgehog/hedgehog.h>  Tutorial contents

The tutorials are meant to demonstrate the usage of the Hedgehog API, and are not meant for obtaining performance.  Preamble

Tutorial 1 - Graph and Task: Simple Hadamard product Tutorial 2 - Multiple inputs, State, State Manager: Hadamard product

Tutorial 3 - Performance and graph reuse Tutorial 4 - Cycle resolution: CPU Matrix Multiplication

Tutorial 5 - GPU Computation and memory management: GPU Matrix Multiplication

Tutorial 6 - MultiGPU Computation and graph bunble: GPU Matrix Multiplication Tutorial 7 - Compile-time analysis Tutorial 8 - Hedgehog extension

Profiling tools in Hedgehog Moving from Hedgehog v.2 to v.3  Credits Alexandre Bardakoff Timothy Blattner Walid Keyrouz Bruno Bachelet LoÃ¯c Yon

Mary Brady Contact us Timothy Blattner (timothy.blattner ( at ) nist.gov) Disclaimer

NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the software in any medium, provided that you keep intact this entire notice. You may improve, modify and create derivative works of the software or any portion of the software, and you may copy and distribute such modifications or works. Modified works should carry a notice stating that you changed the software and should note the date and nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the source of the software.

NIST-developed software is expressly provided âAS IS.â NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE.

You are solely responsible for determining the appropriateness of using and distributing the software, and you assume all risks associated with its use, including but not limited to the risks and costs of program errors, compliance with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of operation. This software is not intended to be used in any situation where a failure could cause risk of injury or damage to property. The software developed by NIST employees is not subject to copyright protection within the United States.

Hedgehog Tutorials

Tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

</link4>

<link5>
Tutorial 1 - Simple Hadamard Product | Hedgehog Tutorials                      Hedgehog Tutorials

AboutPreambleTutorial 1 - Simple Hadamard ProductTutorial 2 - Hadamard Product with Managed StateTutorial 3 - Parallel ReductionTutorial 4 - Matrix Multiplication with cycleTutorial 5 - Matrix Multiplication on NVIDIA GPU with memory managementTutorial 6 - Matrix Multiplication on multiple NVIDIA GPUsTutorial 7 - Compile-time analysisTutorial 8 - Extensibility in HedgehogProfiling toolsMoving from Hedgehog v.2 to Hedgehog v.3

Tutorial 1 - Simple Hadamard Product   Content  Goal Computation Data structure Task Graph Conclusion   Goal

The first tutorial computes the Hadamard product (element-wise product) of two matrices A and B. The computation is made in a block-based fashion to exploit parallelism in Hedgehog.

The base API that is presented:  Create a simple graph, Define a CPU based Task, Push data into the graph and get results out of it,

Do and visualize the computation.   Computation The computation is decomposed as follows:

Decompose the matrices into blocks (handled outside the graph), Do the element-wise product of A and B, and, store the result into C.

Data structure We will use data structures that will wrap the data array plus some convenient accessors:  MatrixData<T, Id, Order>: A matrix,

MatrixBlockData<T, Id, Order>: A matrix block, TripleMatrixBlockData<T, Order>: The corresponding block from matrix A, matrix B and matrix C.

These data structures are specialized with the following elements:  Type: The type of the matrix elements, Id: The matrix identifier, a, b, or, c,

Ord: The way the matrix is ordered, row based, or, column based.   Computation task

In Hedgehog the AbstractTask represents compute kernels. Each task can have multiple input types and multiple output types.

In this example, only one computation task is needed with one input type and one output type: the Hadamard product task.

It has as input the triplet of blocks from the matrices A, B and C, and have as output the block of C filled with the values from element-wise multiplying A and B.

To create a task for Hedgehog, we create a class that will inherit publicly from AbstractTask with the needed input and output:

template<class Type, Order Ord>

class HadamardProduct : public hh::AbstractTask<1, TripletMatrixBlockData<Type, Ord>, MatrixBlockData<Type, 'c', Ord>>

The template declaration reads as follows: the first (1) defines the number of input types, followed by each input type (TripletMatrixBlockData<Type, Ord>) and the rest are the output types (MatrixBlockData<Type, âcâ, Ord>).

The constructor of the HadamardProduct takes two arguments: HadamardProduct(std::string const &name, size_t numberThreads)

: hh::AbstractTask<1, TripletMatrixBlockData<Type, Ord>, MatrixBlockData<Type, 'c', Ord>>(name, numberThreads) {}   name: The name of the task,

numberThreads: The number of threads associated with this task.

We want to compute multiple blocks of A, B and, C at the same time, so we will create a group of HadamardProduct tasks.

This is done by creating multiple instances of the HadamardProduct.

The number of instances is given to the Hedgehog library through the numberThreads parameter in the AbstractTask constructor.

Hedgehog will take care of creating the instances for us, but it needs information on how to âduplicateâ the task, which is done by overriding the âcopyâ method, defined as follows for our HadamardProduct task:

std::shared_ptr<hh::AbstractTask<1, TripletMatrixBlockData<Type, Ord>, MatrixBlockData<Type, 'c', Ord>>>

copy() override { return std::make_shared<HadamardProduct>(this->name(), this->numberThreads()); }

The copy method is made to create a new instance of a specialized AbstractTask from the current one.

So if attributes need to be shared among the task, they need to be transferred via the copy method, in our case, the name of the task and the number of threads.

Because each copy will live on their own thread, if data needs to be shared within a group of tasks then some arrangements may need to be made to ensure thread safety when accessing the shared data such as by sharing locks. For the HadamardProduct task, there is no need to share any data between threads as each TripletMatrixBlockData sent to the task is independent from eachother.

The AbstractTask makes no guarantees for data safety when variables/data is shared by the copy function.

Note here that the copy method is only needed if the numberThreads is greater than 1 (one).

The computation kernel of the task is defined with the method execute:

void execute(std::shared_ptr<TripletMatrixBlockData<Type, Ord>> triplet) override { // Do the computation (found in the tutorial codebase on github)

this->addResult(blockC); }  When a TripletMatrixBlockData<Type, Ord> is sent to the HadamardProduct task, the execute method is fired.

This is where the computation is done, in our case the element-wise product (see the tutorial code for the full implementation).

The call of the addResult method is made to send an output of the task, here a MatrixBlockData<Type, âcâ, Ord>.

The execute method is called for every instance of the input type, taken from the taskâs input queue.

Having multiple instances in this queue, and having numberThreads greater than one enables scaling to multi-core CPUs because each thread will operate on independent TripletMatrixBlockData in parallel.

The only mandatory method definitions from the AbstractTask are the execute methods for each taskâs input type and if the number of thread is more than 1 (one), the copy method.

In the main function we will just instantiate the HadamardProduct<MatrixType, Ord> as follow:

auto hadamardProduct = std::make_shared<HadamardProduct<MatrixType, Ord>>("Hadamard Product", numberThreadHadamard);

A shared_ptr is created to operate within Hedgehog and ensure that memory is reclaimed to avoid leaks.  Other types of Tasks

By default the hh::AbstractTask is using mutexes to protect its datastructure (i.e. input queues), to sleep when there is no work to do, or to wakeup when there is at least one data available.

We have added other types of CPU tasks using atomics instead of mutexes for either the queues, the communication layer, or both.

For all of them, the communication layer (sleep/wakeup mechanism) is made with a std::atomic_flag that the thread will wait on when no data is available. When a data arrives, the flag is notified and the task can resume its execution.

Type of tasks Queue     hh::AbstractMixedTask std::queue protected with a std::mutex.   hh::AbstractAtomicTask

Queue implemented with a simple linked list, where the head and tail are atomic values. It cannot store nullptr, because it is used as default empty node value.

hh::AbstractLimitedAtomicTask

Queue implemented with a ring buffer with a limited capacity. So store can fails (returns false) if the queue is full. During its lifetime it can store at most std::numeric_limits<long long>::max() elements.



These other tasks can be derived like hh::AbstractTask and behave exactly the same way. They also may offer better performance depending on the kind of computer architecture the end-user is targeting.

Graph

The Hedgehog Graph is used to connect nodes together to form a dataflow. The nodes are connected through thread-safe queues that hold data inputs for a task.

Similar to a task, the graph has multiple input types and multiple output types.

In our case only one input type is needed, the triplet of blocks, and as output a block of C matrix:

hh::Graph<1, TripletMatrixBlockData<MatrixType, Ord>, MatrixBlockData<MatrixType, 'c', Ord>> graphHadamard("Tutorial 1 : Hadamard Product");

We will connect the hadamardProduct task to the graphHadamard as follows: graphHadamard.inputs(hadamardProduct);

graphHadamard.outputs(hadamardProduct);  We set the task as input and output of the graph, which mean:

For the input: Every data sent to the graph that corresponds to one of the inputs of the task, will be sent to each task designated as input,

For the output: Every data is sent by the task via addResult will be served as output for the graph.

This is only possible because the task is compatible with the graph:

For the input: A task (or nodes that can accept a data), is compatible with a graph if at least one of its input types is the same as one of the graphâs input types,



For the output: A task (or nodes that can produce a data), is compatible with a graph if at least one of its output types is the same as one of the graphâs output types.

We could have written the code as follows: graphHadamard.input<TripletMatrixBlockData<MatrixType, Ord>>(hadamardProduct);

graphHadamard.output<MatrixBlockData<MatrixType, 'c', Ord>>(hadamardProduct);

but because in this case we connect the task as input and output of the graph for all common types respectively, we donât need to do each connection.



Once the graph is set, the graph can be executed. The function executeGraph is called to spawn the threads. After this call, the graph is ready to accept input data:

graphHadamard.executeGraph();  To push an input data into the graph we call for a triplet of blocks: graphHadamard.pushData(triplet);

When no more data will be pushed into the graph, we notify the graph: graphHadamard.finishPushingData();

Then we can process results blocks as they stream out of the graph: while (auto blockResultVariant = graphHadamard.getBlockingResult()) {

std::cout << *(std::get<std::shared_ptr<MatrixBlockData<MatrixType, 'c', Ord>>>(*blockResultVariant)) << std::endl; }

getBlockingResult blocks the main thread execution until it gets data out of the graph.

When there is no longer data being produced by the graph, getBlockingResult will send nullptr, which will break the while loop.

getBlockingResult() returns a std::shared_ptr<std::variant<Â» containing one of the types of the graphâs output.

The std::get<> allows to get the object of a specific type if the variant holds that type.

The final method to call is waitForTermination to wait for all threads within the graph to join: graphHadamard.waitForTermination();

Here we have the sequence of mandatory calls to create, set, execute, push data, get results, and terminate a graph: // Graph Constructor

hh::Graph<1, TripletMatrixBlockData<MatrixType, Ord>, MatrixBlockData<MatrixType, 'c', Ord>> graphHadamard("Tutorial 1 : Hadamard Product");

// Set The hadamard task as the task that will be connected to the graph inputs graphHadamard.inputs(hadamardProduct);

// Set The hadamard task as the task that will be connected to the graph output graphHadamard.outputs(hadamardProduct);  // Execute the graph

graphHadamard.executeGraph();  // Push the data in the graph graphHadamard.pushData(triplet);  // Notify the graph that no more data will be sent

graphHadamard.finishPushingData();  // Loop over the different resulting block of C

while (auto blockResultVariant = graphHadamard.getBlockingResult()) {}  // Wait for everything to be processed graphHadamard.waitForTermination();

A Hedgehog graph can produce a visualization of their current state, in the dot file format (Profiling tools in Hedgehog).

This visualization is useful to understand, debug, and improve a computation. Here is the code to produce a dot file of the Hadamard graph:

graphHadamard.createDotFile("Tutorial1HadamardProduct.dot", ColorScheme::EXECUTION, StructureOptions::ALL);  And here is the visualization:

The GraphViz dot command-line tool is used to create the visualization: dot -Tpng TutorialHadamardProduct.dot -o TutorialHadamardProduct.png

Conclusion We have seen in this tutorial:  How to create a multithreaded task, What are the taskâs mandatory methods to override,

How to create and run a Hedgehog graph, What are the rules to connect a task to a graph, How to design the Hadamard Product within Hedgehog.

Hedgehog Tutorials

Tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

</link5>

<link6>
Tutorial 7 - Compile-time analysis | Hedgehog Tutorials                      Hedgehog Tutorials

AboutPreambleTutorial 1 - Simple Hadamard ProductTutorial 2 - Hadamard Product with Managed StateTutorial 3 - Parallel ReductionTutorial 4 - Matrix Multiplication with cycleTutorial 5 - Matrix Multiplication on NVIDIA GPU with memory managementTutorial 6 - Matrix Multiplication on multiple NVIDIA GPUsTutorial 7 - Compile-time analysisTutorial 8 - Extensibility in HedgehogProfiling toolsMoving from Hedgehog v.2 to Hedgehog v.3

Tutorial 7 - Compile-time analysis   Content  Context Logic API  Graph representation Tests at compile time Usage of tests   Conclusion

Context In the previous tutorials, we present Hedgehog and its runtime library.

Built-in to Hedgehog, there are transparent compile-time analysis that takes place to ensure that all connections (input/output nodes of a graph and edges) are valid.

In addition to that, we have added a tool library that can be used to control the graph structure at compile-time.

In order to do as much computation as possible at compile-time we have developed this library around the modifier constexpr.

In essence, it indicates to the compiler that this code can be executed at compile-time.

This modifier has been added to the c++ 11 norm and enriched since then.

The latest additions are important for the library (constexpr std::vector and constexpr std::string).

That is why only the newest compilers that support these features can be used, for example g++ 12.1.  Logic

The library is generally used by using the following three steps: 1) Create the representation of the compilation at compile time,

2) Run the tests over the graph representation, 3) Show the errors found or transform the graph representation to the runtime graph.

We need this compile-time representation in addition to the runtime graph because the graph canât be represented at compile-time.

This is a limitation of the language, for example the std::shared_ptr can not be used at compile-time.

The API used at compile-time has been designed to mimic the runtime one and has been enriched to query the graph structure.  API Graph representation

In order to build the graph representation, we follow the same logic as the runtime library.

First, the nodes and the graph representation need to be instantiated, and second, the graph representation can be built.

For example if we want to represent this task and graph: class TaskIntInt : public hh::AbstractTask<1, int, int> { public:

void execute(std::shared_ptr<int> data) override { this->addResult(data); } };  class GraphIntInt : public hh::Graph<1, int, int> { public:

explicit GraphIntInt(std::string const &name) : hh::Graph<1, int, int>(name) {} };  to build this graph:

We declare the compile-time representation as: hh_cx::Node<TaskIntInt> node1("node1"), hh_cx::Graph<GraphIntInt> graph{"graph"};

The first template parameter of a hh_cx::Node and the template parameter of a hh_cx::Graph is the type these nodes represent at compile-time.

The rest of the template parameters of the hh_cx::Node are discussed later.

A state-manager, an internal graph, or an execution pipeline are also represented with a hh_cx::Node at compile-time.

In the case of an internal graph, it is considered as a black box, a single node, only the input and output types and its connections matters and are represented at compile-time.

The nodes are created with an identifier (ânode1â in the example).

This identifier needs to be unique and is used later on to do the mapping between the compile-time representation and the runtime node.

Once the nodes are instantiated, we can build the graph representation with an API like the runtime one: hh_cx::Node<TaskIntInt>

node1("node1"), node2("node2"), node3("node3"), node4("node4"), node5("node5"), node6("node6"), node7("node7");

hh_cx::Graph<GraphIntInt> graph{"graph"};  graph.inputs(node1); graph.edges(node1, node2); graph.edges(node2, node3); graph.edges(node2, node5);

graph.edges(node3, node4); graph.edges(node3, node5); graph.edges(node4, node1); graph.edges(node4, node7); graph.edges(node5, node6);

graph.edges(node6, node2); graph.outputs(node7);  Once the graph is built, we can associate it to test:

auto dataRaceTest = hh_cx::DataRaceTest < GraphIntInt > {}; auto cycleTest = hh_cx::CycleTest < GraphIntInt > {}; graph.addTest(&dataRaceTest);

graph.addTest(&cycleTest);  Details about tests are given in a later section.

This graph creation needs to be wrapped in a constexpr function (callable) to be used by the library as shown bellow:

constexpr auto constructGraphInts() { hh_cx::Node<TaskIntInt> node1("node1"), node2("node2"), node3("node3"),

node4("node4"), node5("node5"), node6("node6"), node7("node7");  hh_cx::Graph<GraphIntInt> graph{"graph"};  graph.inputs(node1);

graph.edges(node1, node2); graph.edges(node2, node3); graph.edges(node2, node5); graph.edges(node3, node4); graph.edges(node3, node5);

graph.edges(node4, node1); graph.edges(node4, node7); graph.edges(node5, node6); graph.edges(node6, node2); graph.outputs(node7);

auto dataRaceTest = hh_cx::DataRaceTest < GraphIntInt > {}; auto cycleTest = hh_cx::CycleTest < GraphIntInt > {}; graph.addTest(&dataRaceTest);

graph.addTest(&cycleTest); return graph; }  Tests at compile-time The goal of this tool library is to test a graph structure at compile time.

We have built an abstraction to define the tests (hh_cx::AbstractTest).

This abstraction has been used to define the two tests available in the library; the cycle detection test and the data race test.

Cycle detection test Cycles are authorised in Hedgehog but needs extra care (cf. Tutorial 4).

This test is meant to detect cycles with the Tarjan and Johnson algorithms.

Once these cycles are detected, they are filtered to only present the cycles in which no nodes have implemented the canTerminate method.

This test only detect the presence of the method in one of the nodes, but not the validity of the condition in it !

This is only meant to determine if the end-user has not forgotten to take care of it. In the previous example there are cycles between the nodes:

node1 -> node2 -> node3 -> node4 -> node1 node2 -> node3 -> node5 -> node6 -> node2 node2 -> node5 -> node6 -> node2

And once the test runs it detects them and returns (we cover later how we produce this output):

Cycles found, the canTerminate() method needs to be defined for each of these cycles. node1 -> node2 -> node3 -> node4 -> node1

node2 -> node3 -> node5 -> node6 -> node2 node2 -> node5 -> node6 -> node2  If we change the definition of the task to:

class TaskIntInt : public hh::AbstractTask<1, int, int> { public:

explicit TaskIntInt(std::string const & name) : hh::AbstractTask<1, int, int>(name){}

void execute(std::shared_ptr<int> data) override { this->addResult(data); } bool canTerminate() const override{ return false; } };

This solves the problem for the test, the graph is considered as valid while it is not at runtime: the task never terminates. Data race test

This test is meant to detect data races that can occur if a non-const piece of data is sent to more than one node.

For memory, when a piece of data is sent via an addResult, the shared_ptr wrapping it is copied to each of the successors.

In the example we have multiple potential data races:  node2 -> node3 / node5 for the int type node3 -> node5 / node4 for the int type

node4 -> node1 / node7 for the int type  They are found by the test: Possible data races found: node2 -> node3 (int) node2 -> node5 (int)

node3 -> node5 (int) node3 -> node4 (int) node4 -> node1 (int) node4 -> node7 (int)  If we were to not transfer int but int const such as:

class TaskCIntCInt : public hh::AbstractTask<1, int const, int const> { public:

explicit TaskCIntCInt(std::string const &name) : hh::AbstractTask<1, int const, int const>(name) {}

void execute(std::shared_ptr<int const> data) override { this->addResult(data); } };

class GraphCIntCInt : public hh::Graph<1, int const, int const> { public:

explicit GraphCIntCInt(std::string const &name) : hh::Graph<1, int const, int const>(name) {} };  constexpr auto constructGraphConstInts() {

hh_cx::Node<TaskCIntCInt> node1("node1"), node2("node2"), node3("node3"), node4("node4"), node5("node5"), node6("node6"), node7("node7");

hh_cx::Graph<GraphCIntCInt> graph{"graph"};  graph.inputs(node1); graph.edges(node1, node2); graph.edges(node2, node3); graph.edges(node2, node5);

graph.edges(node3, node4); graph.edges(node3, node5); graph.edges(node4, node1); graph.edges(node4, node7); graph.edges(node5, node6);

graph.edges(node6, node2); graph.outputs(node7);  auto dataRaceTest = hh_cx::DataRaceTest < GraphCIntCInt > {};

auto cycleTest = hh_cx::CycleTest < GraphCIntCInt > {}; graph.addTest(&dataRaceTest); graph.addTest(&cycleTest); return graph; }

There is no problem found by the test anymore because the values (here int) are not mutable.

Finally, it is possible to declare [a] input type[s] as read-only.

We have added this feature to represent a node that receives a non-const data with a kernel that does not write the received value.

The read-only input types are declared on the template parameters of the nodes. In our example, we can declare the int input node as follows:

hh_cx::Node<TaskIntInt, int> node1("node1"), node2("node2"), node3("node3"), node4("node4"), node5("node5"), node6("node6"), node7("node7");

With this declaration, no problem is found by the test. User-defined test It is possible to add your own test.

A test is created by implementing the hh_cx::AbstractTest abstraction.

For example, we can create a test that will print the critical path of a graph.

In order to do so, we need to have some kind of representation of the weight of the nodes.

To add metadata to the nodes for the static analysis we have created the hh_cx::PropertyMap. Its template parameter is the type of metadata it holds.

It maps the node identifier to the metadata : hh_cx::PropertyMap<double> propertyMap; propertyMap.insert("node1", 1); propertyMap.insert("node2", 2);

propertyMap.insert("node3", 3); propertyMap.insert("node4", 4); propertyMap.insert("node5", 5); propertyMap.insert("node6", 6);

propertyMap.insert("node7", 12);  Once we have associated these metadata we can reuse the test in our tests.

The hh_cx::AbstractTest abstraction needs the test name at construction and needs the *void test(hh_cx::Graph const \*graph)* method implemented.

In it the *graphValid* setter is used to set the graph's validity and *appendErrorMessage* is used to create the report. The test can be written as:

template<class GraphType> class TestCriticalPath : public hh_cx::AbstractTest<GraphType> { private: double_t maxPathValue_ = 0,

currentPathValue_ = 0;  hh_cx::PropertyMap<double> propertyMap_;  hh_cx::Graph<GraphType> const *graph_ = nullptr;

std::vector<hh_cx::behavior::AbstractNode const *> criticalVector_{}, visited_{};  public:

constexpr explicit TestCriticalPath(hh_cx::PropertyMap<double> propertyMap)

: hh_cx::AbstractTest<GraphType>("Critical Path"), propertyMap_(std::move(propertyMap)) {}  constexpr ~TestCriticalPath() override = default;

constexpr void test(hh_cx::Graph<GraphType> const *graph) override { graph_ = graph;  auto const &inputNodeMap = graph->inputNodes();

for (auto const &type : inputNodeMap.types()) { for (auto const &inputNode : inputNodeMap.nodes(type)) { this->visitNode(inputNode); } }

if (criticalVector_.empty()) { this->graphValid(true); } else { this->graphValid(false);  this->graphValid("The critical path is:\n\t");

this->appendErrorMessage(criticalVector_.front()->name());

for (size_t criticalNodeId = 1; criticalNodeId < criticalVector_.size(); ++criticalNodeId) { this->appendErrorMessage(" -> ");

this->appendErrorMessage(criticalVector_.at(criticalNodeId)->name()); } }; }  private:

constexpr void visitNode(hh_cx::behavior::AbstractNode const *node) { if (std::find(visited_.cbegin(), visited_.cend(), node) == visited_.cend()) {

currentPathValue_ += propertyMap_.property(node->name()); visited_.push_back(node);

if (std::find(visited_.cbegin(), visited_.cend(), node) != visited_.cend()) { if (currentPathValue_ > maxPathValue_) {

maxPathValue_ = currentPathValue_; criticalVector_.clear(); criticalVector_ = visited_; } }

for (auto const &neighbor : graph_->adjacentNodes(node)) { visitNode(neighbor); }  currentPathValue_ -= propertyMap_.property(node->name());

visited_.pop_back(); } } };  The graph construction is: constexpr auto constructGraphIntCustomTest() { hh_cx::Node<TaskIntInt> node1("node1"),

node2("node2"), node3("node3"), node4("node4"), node5("node5"), node6("node6"), node7("node7");

hh_cx::Graph<GraphIntInt> graph{"Custom test graph"};  graph.inputs(node1); graph.edges(node1, node2); graph.edges(node2, node3);

graph.edges(node2, node5); graph.edges(node3, node4); graph.edges(node3, node5); graph.edges(node4, node1); graph.edges(node4, node7);

graph.edges(node5, node6); graph.edges(node6, node2); graph.outputs(node7);  hh_cx::PropertyMap<double> propertyMap;  propertyMap.insert("node1", 1);

propertyMap.insert("node2", 2); propertyMap.insert("node3", 3); propertyMap.insert("node4", 4); propertyMap.insert("node5", 5);

propertyMap.insert("node6", 6); propertyMap.insert("node7", 12);  auto criticalPathTest = TestCriticalPath<GraphIntInt>(propertyMap);

graph.addTest(&criticalPathTest); return graph; }  and produce: Custom test graph is Valid ? false-> The critical path is:

node1 -> node2 -> node3 -> node4 -> node7  Usage of tests Run the tests - Defroster creation To run the tests, we need to create a defroster.

The defroster is the data structure that is made to transfer the data from compile-time to runtime.

It also applies the tests on the graph and extracts the graphâs structure that will be used later on.

To create a defroster a user can use the hh_cx::createDefroster function as follows:

constexpr auto defrosterInt = hh_cx::createDefroster<&constructGraphInt>();

constexpr auto defrosterCanTerminate = hh_cx::createDefroster<&constructGraphWithCanTerminate>();

constexpr auto defrosterROInt = hh_cx::createDefroster<&constructGraphROInt>();

constexpr auto defrosterConstInt = hh_cx::createDefroster<&constructGraphConstInt>();

constexpr auto defrosterCustomTest = hh_cx::createDefroster<&constructGraphIntCustomTest>();  Usage of defroster

The defroster can be used at compile time to either stop the compilation with a std::static_assert if the graph is not valid:

static_assert(!defrosterInt.isValid(), "The graph should not be valid"); // or

static_assert(!defrosterCustomTest.isValid(), "The graph should not be valid");  or branch the compilation of some code with an if constexpr:

if constexpr (defrosterCanTerminate.isValid()) { std::cout << "The graph with the canTerminate method defined is valid" << std::endl; }else {

std::cout << "The graph with the canTerminate method defined is not valid" << std::endl; }

A real use case could be to print the report if the graph is not valid:

if constexpr (!defrosterInt.isValid()) { std::cout << defrosterInt.report() << std::endl; } else { /*[...]*/ }

If the graph is valid, we can transform the compile-time representation to a runtime graph.

To do so, we need to instantiate the runtime node and map them to the compile-time graphâs nodes representation:

if constexpr (!defrosterROInt.isValid()) { std::cout << defrosterROInt.report() << std::endl; } else { auto graph = defrosterROInt.map(

"node1", std::make_shared<TaskIntInt>("Task1"), "node2", std::make_shared<TaskIntInt>("Task2"), "node3", std::make_shared<TaskIntInt>("Task3"),

"node4", std::make_shared<TaskIntInt>("Task4"), "node5", std::make_shared<TaskIntInt>("Task5"), "node6", std::make_shared<TaskIntInt>("Task6"),

"node7", std::make_shared<TaskIntInt>("Task7") ); graph->createDotFile("GraphIntInt.dot"); }

The dot file created is the same as the one presented in this previous section. The graph object can then be used as a runtime graph.  Conclusion

In this tutorial we have seen how to:  represent a graph at compile-time, run test[s] on it, use the test[s] results,

create a runtime graph from the compile-time structure representation.          Hedgehog Tutorials

Tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

</link6>

<link7>
Tutorial 5 - Matrix Multiplication on NVIDIA GPU with memory management | Hedgehog Tutorials                      Hedgehog Tutorials

AboutPreambleTutorial 1 - Simple Hadamard ProductTutorial 2 - Hadamard Product with Managed StateTutorial 3 - Parallel ReductionTutorial 4 - Matrix Multiplication with cycleTutorial 5 - Matrix Multiplication on NVIDIA GPU with memory managementTutorial 6 - Matrix Multiplication on multiple NVIDIA GPUsTutorial 7 - Compile-time analysisTutorial 8 - Extensibility in HedgehogProfiling toolsMoving from Hedgehog v.2 to Hedgehog v.3

Tutorial 5 - Matrix Multiplication on NVIDIA GPU with memory management   Content  Goal Computation Data structure Memory management Task Graph

Conclusion   Goal

The goal of this tutorial is to create tasks that launch NVIDIA CUDA kernels and how to use the Hedgehogâs Memory Management tool.  Computation

The computation follows the same logic and steps as tutorial 4.

In this tutorial, we will port only part of the computation onto the GPU: the âproduct taskâ.

Because we are dealing with the GPU, data motion and the amount of data in the GPU must be taken care of:

Data motion: The process of sending data between address spaces (CPU to GPU). This can be costly, so the data motion is invoked asynchronously,

Data amount limitation: The memory on a GPU is limited, so for big matrices, they wonât fit in GPU memory, the amount of computation in-flight within a graph will be directed by the amount of memory available to the GPU.

3 GPU tasks will be added:  âCudaCopyInGPUâ: Responsible to send the block from the CPU to the GPU,

âCudaProductTaskâ: Responsible to do the partial product on GPU and produce the temporary block,

âCudaCopyOutGPUâ: Responsible to get back the block from the GPU to the CPU.

The computation kernel for the âproduct taskâ calls the cuBLAS routines. These routines follow a column-based storage model.

So the blocks will be stored in column-major order. The traversal of the matrices is also very important to how much memory is consumed.

For matrix multiplication, the earliest time a block can be released for matrices A or B is when it has been fully multiplied by its matching row or column of blocks, respectively. Having this traversal pattern is key to operating on matrices that do not necessarily fit in GPU memory, and will be important in understanding when memory can be recycled. This traversal pattern is shown below:

The remaining tasks and states, will be taken from tutorial 4. Data structure

A data structure âCudaMatrixBlockDataâ has been designed for this tutorial.

It inherits from âMatrixBlockDataâ, because it is a block and stores more metadata related to the GPU computation.

It also inherits from âManagedMemoryâ from the Hedgehog API, to allow Hedgehog to manage this memory:

class CudaMatrixBlockData : public MatrixBlockData<Type, Id, Order::Column>, public hh::ManagedMemory;  The others are the same as tutorial 4.

Memory Management The memory manager is a tool in Hedgehog that helps developers to limit the amount of data flowing in a graph.

It consists of a pool and a way to serve instances of an object into a Task and recycle its memory.

If there are no instances available in the pool, then the task will block until a new instance is available.

Additionally, ManagedMemory can specify the state of the memory, to indicate to the memory manager when to recycle the memory. This is useful if the memory should be reused multiple times before it is recycled.

Setup There is one mandatory parameter that is needed to create a memory manager, the pool capacity: explicit MemoryManager(size_t const &capacity)

This pool capacity will set the maximum number of instances of an object that will flow into the graph from this memory manager.

Hedgehog defines two memory managers:

âMemoryManagerâ: the base memory manager, the pool will be initialized by calling only the default constructor of the data defined by the user,

âStaticMemoryManagerâ: the static memory manager, the pool will be initialized by calling the specified constructor of the data defined by the user.



In this example, and in general, especially with CUDA related data, we encourage to use the static memory manager to avoid GPU device synchronization during the execution, which is caused when CUDA allocates memory.

The type managed by the memory manager is set by defining:  The only template type of the âMemoryManagerâ,

The first template type of the âStaticMemoryManagerâ.

In order for the âStaticMemoryManagerâ to choose the right constructor at initialization, the signature types must match the other âStaticMemoryManagerâ template types.

For example, letâs define a class âHouseâ as follows: class House : public ManagedMemory{ private: std::vector<int> *family_ = nullptr,

*pet_ = nullptr;  size_t ttl_ = 0;  public: House () = default; House(size_t familySize, size_t petSize, size_t ttl ){

family_ = new std::vector<int>(familySize); pet_ = new std::vector<int>(petSize); std::iota(family_->begin(), family_->end(), 0);

std::iota(pet_->begin(), pet_->end(), family_->size()); ttl_ = ttl > 0 ? ttl: 1; }

House(size_t familySize, size_t petsSize): House(familySize, petsSize, 1){}  ~House() final { delete family_; delete pet_; } };

If we want to initialize the pool by calling the following constructor: House(size_t familySize, size_t petSize, size_t ttl )

the type of the âStaticMemoryManagerâ will be: StaticMemoryManager<House, size_t, size_t, size_t >

If we want to initialize the pool by calling the following constructor: House(size_t familySize, size_t petSize )

the type of the âStaticMemoryManagerâ will be: StaticMemoryManager<House, size_t, size_t>

Then when we construct the âStaticMemoryManagerâ, the first constructor parameter is always the pool capacity, then the remaining constructor parameters are passed to the managed data constructor, so:

// Fill the pool with 10 instances of House calling the constructor House(1, 2, 3) for each instance

StaticMemoryManager<House, size_t, size_t, size_t > smm(10, 1, 2, 3);

// Fill the pool with 42 instances of House calling the constructor House(98, 1) for each instance

StaticMemoryManager<House, size_t, size_t > smm(42, 98, 1);  Recycling mechanism All the memory managers come with a recycling mechanism.

When ManagedMemory::returnToMemoryManager() is invoked, the recycling mechanism is used which consists of calling the following virtual methods, in the following order:



ManagedMemory::postProcess(): Mechanism called by Hedgehog when the node returns the memory before it is tested for being recycled (for example in the case the ManagedMemory is returned to the MemoryManager multiple times before being recycled (based on return of canBeRecycled) and sent back to the Pool).

ManagedMemory::canBeRecycled(): Boolean method to determine if the ManagedMemory can be recycled, and sent back to the Pool.

ManagedMemory::clean(): Recycle the ManagedMemory. The data given by the MemoryManager is default constructed the first time. If specialized class attributes are allocated, they should be deallocated in this method, to avoid memory leaks, to return the ManagedMemory to the same state as default construction.



The same behavior, is used by the StaticMemoryManager, only, no other allocation should be made by the user, so ManagedMemory::clean() can be used to clean the data if needed to be reused later on.

The managed memory will be deallocated during the pool destruction by calling the destructor of the specialed ManagedMemory. Therefore, any memory allocated within constructors that are used by the StaticMemoryManager should be properly deallocated in their destructor.

Additionally, there is a fourth function for customizing the behavior for memory: ManagedMemory::preProcess(), this is called prior to sending memory from the memory manager to a task. One use of this is to initialize the memory, state, or other operations. One such example is prefetching CUDA unified memory to a particular location. This functionality is not used in this example.

Usage in tutorial

We are using the memory manager to throttle the memory on the GPU so that we stay within the limits of GPU memory. In addition, we use the âStaticMemoryManagerâ to pre-allocate a pool of CUDA memories rather than using dynamic allocation. Dynamic GPU allocation may cause GPU device synchronization, resulting in reductions in performance.

// MemoryManagers auto cudaMemoryManagerA =

std::make_shared<hh::StaticMemoryManager<CudaMatrixBlockData<MatrixType, 'a'>, size_t>>(nBlocks + 4, blockSize); auto cudaMemoryManagerB =

std::make_shared<hh::StaticMemoryManager<CudaMatrixBlockData<MatrixType, 'b'>, size_t>>(pBlocks + 4, blockSize); auto cudaMemoryManagerProduct =

std::make_shared<hh::StaticMemoryManager<CudaMatrixBlockData<MatrixType, 'p'>, size_t>>(8, blockSize);

each of the memory managers call the âCudaMatrixBlockDataâ constructor with different pool capacity (nBlocks + 4, or pBlocks + 4 or 8):

explicit CudaMatrixBlockData(size_t blockSize)  The pool capacity is selected based on the computation.

For matrix multiplication, it represents the number of times that memory is going to be used plus some buffering.

This allows for enough memory to be in-flight to recycle the memory in time, and provide enough parallelism.

If too little memory is allocated, then the algorithm may deadlock due to memory never getting recycled in time.

Memory data is received from the memory managers from the âexecuteâ method of âCudaCopyInGpuâ:

void execute(std::shared_ptr<MatrixBlockData<MatrixType, Id, Order::Column>> ptr) override { // Getting the memory from the memory manager

auto block = std::dynamic_pointer_cast<CudaMatrixBlockData<MatrixType, Id>>(this->getManagedMemory()); // Do stuff this->addResult(block); }

Then we use it in the âCudaProductTaskâ, to do the actual product on the GPU.

After the product has completed, the memory is returned to the memory manager from within the CudaProductTaskâs execute method:

void execute(std::shared_ptr<std::pair<CudaMatrixBlockData<MatrixType, 'a'>, CudaMatrixBlockData<MatrixType, 'b'>> ptr) override {

auto matA = ptr->first; auto matB = ptr->second; // Do stuff matA->returnToMemoryManager(); // Return the memory to the memory manager

matB->returnToMemoryManager(); // Return the memory to the memory manager // Do stuff }

The CudaProductTask also will receive memory from its memory manager, which gets returned to the CudaCopyOutGpu task. Calling returnToMemoryManager will first post process the memory updating its time to live by calling ManagedMemory::postProcess, and then ManagedMemory::canBeRecycled. If canBeRecycled returns true, then the memory is added back into the memory managerâs pool.

Computation task CUDA tasks wonât inherit from âAbstractTaskâ but will inherit from âAbstractCUDATaskâ.

âAbstractCUDATasksâ are âAbstractTasksâ (they inherit from âAbstractTaskâ).

âAbstractCUDATasksâ holds additional attributes that are needed for GPU computation; the device id, cuda stream, and the ability to enable peer access between multiple devices.

During task initialization, the following steps take place:

call âcudaSetDeviceâ (this binds the thread to the CUDA device, all subsequent calls from this thread will be on that device),

create the stream for the execution âcudaStreamCreateâ (this binds the stream to that device, to be used by CUDA functions),

enable peer access if needed.  During task shutdown, the stream will be destroyed with: âcudaStreamDestroyâ.

If an extra initialization is needed, âinitializeCudaâ is overloaded.

Per symmetry, if an extra shutdown step is needed, the âshutdownCudaâ is overload.

The thread that operates the Cuda task will never leave that task, which means it is bound to the device Id for the task when cudaSetDevice was called.

Therefore, any functions that are called within initializeCuda, execute, and shutdownCuda will be bound to that device Id.

Here is the order of execution for the âCudaProductTaskâ:

âcudaSetDeviceâ, âcudaStreamCreateâ, (optional)âcudaDeviceCanAccessPeerâ, are called automatically by Hedgehog,

âinitializeCudaâ, which calls âcublasCreate_v2â and âcublasSetStream_v2â. Creates the handle needed to call âcublasSgemm_v2â,

âexecuteâ that will call the execution kernel: âcublasSgemm_v2â for every pair of blocks from a and b,

âshutdownCudaâ, that will call âcublasDestroy_v2â, âcudaStreamDestroyâ, called automatically by Hedgehog.  The corresponding code is:

template<class Type> class CudaProductTask : public hh::AbstractCUDATask< 1,

std::pair<std::shared_ptr<CudaMatrixBlockData<Type, 'a'>>, std::shared_ptr<CudaMatrixBlockData<Type, 'b'>>>, CudaMatrixBlockData<Type, 'p'> > {

private: size_t countPartialComputation_ = 0; private: cublasHandle_t handle_ = {};  public:

explicit CudaProductTask(size_t countPartialComputation, size_t numberThreadsProduct = 1) : hh::AbstractCUDATask< 1,

std::pair<std::shared_ptr<CudaMatrixBlockData<Type, 'a'>>, std::shared_ptr<CudaMatrixBlockData<Type, 'b'>>>, CudaMatrixBlockData<Type, 'p'>

>("CUDA Product Task", numberThreadsProduct, false, false), countPartialComputation_(countPartialComputation) {}  void initializeCuda() override {

checkCudaErrors(cublasCreate_v2(&handle_)); checkCudaErrors(cublasSetStream_v2(handle_, this->stream())); }

void shutdownCuda() override { checkCudaErrors(cublasDestroy_v2(handle_)); }  void execute(std::shared_ptr<

std::pair<std::shared_ptr<CudaMatrixBlockData<Type, 'a'>>, std::shared_ptr<CudaMatrixBlockData<Type, 'b'>> >> ptr) override { // [...]

if constexpr (std::is_same<Type, float>::value) { checkCudaErrors( cublasSgemm_v2(handle_, CUBLAS_OP_N, CUBLAS_OP_N,

matA->blockSizeHeight(), matB->blockSizeWidth(), matA->blockSizeWidth(), &alpha, (float *) matA->blockData(), matA->leadingDimension(),

(float *) matB->blockData(), matB->leadingDimension(), &beta, (float *) res->blockData(), res->leadingDimension()) );

} else if (std::is_same<Type, double>::value) { checkCudaErrors( cublasDgemm_v2(handle_, CUBLAS_OP_N, CUBLAS_OP_N,

matA->blockSizeHeight(), matB->blockSizeWidth(), matA->blockSizeWidth(), &alpha, (double *) matA->blockData(), matA->leadingDimension(),

(double *) matB->blockData(), matB->leadingDimension(), &beta, (double *) res->blockData(), res->leadingDimension()) ); // [...]

matA->returnToMemoryManager(); matB->returnToMemoryManager(); this->addResult(res); } std::shared_ptr<hh::AbstractTask< 1,

std::pair<std::shared_ptr<CudaMatrixBlockData<Type, 'a'>>, std::shared_ptr<CudaMatrixBlockData<Type, 'b'>>>,

CudaMatrixBlockData<Type, 'p'>>> copy() override { return std::make_shared<CudaProductTask>(countPartialComputation_, this->numberThreads()); } };

The other defined tasks âCudaCopyInGPUâ and âCudaCopyOutGPUâ do not need extra initialize or shutdown steps, so âinitializeCudaâ and âshutdownCudaâ are not overloaded.

Hedeghog proposes a function âcheckCudaErrorsâ that accepts a âcudaError_tâ or a âcublasStatus_tâ, to test the value, and exit if an error occurs, which is based on the checkCudaErrors function from the NVIDIA Cuda toolkit.

The other tasks, and state managers are reused from tutorial 4.  Graph Here is the final graph:   Conclusion We have seen in this tutorial:

How to do some computation on the GPU with Hedgehog using âAbstractCUDATaskâ,

How to manage memory inside a Hedgehog graph with the âMemory Managerâ family of tools.          Hedgehog Tutorials

Tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

</link7>

<link8>
Tutorial 8 - Extensibility in Hedgehog | Hedgehog Tutorials                      Hedgehog Tutorials

AboutPreambleTutorial 1 - Simple Hadamard ProductTutorial 2 - Hadamard Product with Managed StateTutorial 3 - Parallel ReductionTutorial 4 - Matrix Multiplication with cycleTutorial 5 - Matrix Multiplication on NVIDIA GPU with memory managementTutorial 6 - Matrix Multiplication on multiple NVIDIA GPUsTutorial 7 - Compile-time analysisTutorial 8 - Extensibility in HedgehogProfiling toolsMoving from Hedgehog v.2 to Hedgehog v.3

Tutorial 8 - Extensibility in Hedgehog   Content  Context Architecture Creating a new node by deriving the API

Creating a new type of node (advanced users) Conclusion   Context

Hedgehog has been meant to be fairly easy to extend depending on different types of needs.

There are 3 main extension points with increasing levels of complexity:

Deriving from our API nodes to create your own nodes that shares the base logic with an existing node,

Creating a new implementation for our coreâs abstractions if you want to change the abstractions behaviors,

Creating a new node/core if you need a Hedgehog node that does not work as the one already implemented.

To showcase and explain these extension points we need to first present the Hedgehog architecture.  Architecture

Hedgehog is decomposed into three main parts:  the API (namespace hh) defines the high-level objects used by most end-users,

the behavior (namespace hh::behavior) defines the shared methods existing in the API objects,

the cores (namespace hh::core) is the place where the low-level functionality is implemented.

The main idea was to make a simple-to-use library by only exposing what is useful to most users.

For example, most users do not need to manipulate each of the mutexes in the library. And that explains the dichotomy between the API and the cores.

Furthermore, most IDEs can present the methods that can/need to be defined to create objects.

In order to limit this list we need to âhideâ the less useful methods, hence the separation between the API and the core.

The behavior classes define the methods that are shared amongst different API classes.

These behaviors are not meant to be used as is, that is why they are hidden in a specific namespace to not expose them to most users.

In terms of design patterns:  The logic relationship between the nodes and the graph is a composite structural design pattern.

The relationship between the API and the behavior classes are following a template method behavioral design patterns.

The core is designed to follow a template method behavioral design pattern and the bridge structural design pattern.

We present these patterns in the following sections and different methodologies for how to extend the libary.

Creating a new node by deriving the API This type of extension is made to create a type of node that follows the same logic of an existing node.

For example, in preamble we have presented the logic of an AbstractTask.

This logic remains for the CUDA tasks, which is why to create the hh::AbstractCUDATask we simply derived from hh:: AbstractTask:

template<size_t Separator, class ...AllTypes> class AbstractCUDATask : public AbstractTask<Separator, AllTypes...>;

Another example is the work of Jane Liu, a student that worked at NIST during the Summer Undergraduate Research Fellowship, who implemented real-time capabilities into the library by creating an abstract priority task.

To do so, she has chosen to create the following: #include <pthread.h> #include <sched.h> #include "hedgehog/hedgehog.h"  namespace hh {

enum class Policy {SchedFIFO = SCHED_FIFO, SchedRR = SCHED_RR, SchedOther = SCHED_OTHER};  template<size_t Separator, class ...AllTypes>

class AbstractPriorityTask : public hh::AbstractTask<Separator, AllTypes ...> { private: Policy policy_; const struct sched_param *param_;  public:

AbstractPriorityTask(std::string const &name, size_t numberThreads, Policy policy, const sched_param *param) :

hh::AbstractTask<Separator, AllTypes ...>(name, numberThreads), policy_(policy), param_(param) {}

AbstractPriorityTask(Policy policy, const sched_param *param)

: hh::AbstractPriorityTask<Separator, AllTypes ...>("AbstractPriorityTask", 1, policy, param) {}

AbstractPriorityTask(std::string const &name, Policy policy, const sched_param *param)

: hh::AbstractPriorityTask<Separator, AllTypes ...>(name, 1, policy, param) {}  AbstractPriorityTask(

std::shared_ptr<core::CoreTask<Separator, AllTypes ...>> taskCore, Policy policy, const sched_param *param)

: hh::AbstractTask<Separator, AllTypes ...>(taskCore), policy_(policy), param_(param) {}  ~AbstractPriorityTask() = default;

[[nodiscard]] Policy policy() const { return policy_; } [[nodiscard]] sched_param const *param() const { return param_; }

virtual void initialize() { int int_policy = (int) policy_; if (pthread_setschedparam(pthread_self(), int_policy, param_)) {

std::cerr << "Failed to set thread scheduling: " << std::strerror(errno) << std::endl; } } };  }

This task abstraction is only usable if pthread is accessible. It uses the initialize method to set the real-time properties of this task for this thread.

Modifying a node by changing its coreâs abstraction implementor

As we have mentioned before, the cores are built by using the bridge structural pattern.

If we look at the class diagram of the nodeâs abstraction for receiving data , it looks like this:

The CoreTask and the CoreGraph inherits both from the ReceiverAbstraction but uses different implementors: QueueReceiver and GraphReceiver respectively.

Here is a list of other abstractions that follows this bridge patterns:  ReceiverAbstraction to receive data, SenderAbstraction to send data,

NotifierAbstraction to notify successor nodes that a data is present, SlotAbstraction to accept the message sent by the notifier,

ExecuteAbstraction to present how the data are processed by the node.

We can use these different bridges to customize the implementation of this abstraction.

For example, if we want to use a priority queue instead of a normal queue we can customize the implementation of the receiver:

template<class Input> requires std::totally_ordered<Input> class PriorityQueueReceiver : public hh::core::implementor::ImplementorReceiver<Input> {

private: struct CustomSharedInputGreater {bool operator()(auto const & lhs, auto const & rhs) { return *lhs > *rhs;} } ;

using QueueType = std::priority_queue<std::shared_ptr<Input>, std::vector<std::shared_ptr<Input>>, CustomSharedInputGreater>;

std::unique_ptr<QueueType> const queue_ = nullptr; ///< Queue storing to be processed data

std::unique_ptr<std::set<hh::core::abstraction::SenderAbstraction<Input> *>> const senders_ = nullptr; ///< List of senders attached to this receiver

size_t maxSize_ = 0; ///< Maximum size attained by the queue  std::mutex queueMutex_{}, sendersMutex_{}; public: explicit PriorityQueueReceiver()

: queue_(std::make_unique<QueueType>()), senders_(std::make_unique<std::set<hh::core::abstraction::SenderAbstraction<Input> *>>()) {}

virtual ~PriorityQueueReceiver() = default; bool receive(std::shared_ptr<Input> data) final { std::lock_guard<std::mutex> lck(queueMutex_);

queue_->push(data); maxSize_ = std::max(queue_->size(), maxSize_); return true; }

[[nodiscard]] bool getInputData(std::shared_ptr<Input> &data) override { std::lock_guard<std::mutex> lck(queueMutex_); assert(!queue_->empty());

data = queue_->top(); queue_->pop(); return true; } [[nodiscard]] size_t numberElementsReceived() override {

std::lock_guard<std::mutex> lck(queueMutex_); return queue_->size(); }

[[nodiscard]] size_t maxNumberElementsReceived() const override { return maxSize_; }  [[nodiscard]] bool empty() override {

std::lock_guard<std::mutex> lck(queueMutex_); return queue_->empty(); }

[[nodiscard]] std::set<hh::core::abstraction::SenderAbstraction<Input> *> const &connectedSenders() const override { return *senders_; }

void addSender(hh::core::abstraction::SenderAbstraction<Input> *const sender) override { std::lock_guard<std::mutex> lck(sendersMutex_);

senders_->insert(sender); }  void removeSender(hh::core::abstraction::SenderAbstraction<Input> *const sender) override {

std::lock_guard<std::mutex> lck(sendersMutex_); senders_->erase(sender); } };

The definition of a MultiPriorityQueueReceivers is made to manage all input types from a node.

If we want to have a customizable abstraction we need to automatically deduce the type of MultiPriorityQueueReceivers from the template arguments of a task.

To do so we need to create a trait and a helper to do the conversion automatically: template<class Inputs>

struct MultiPriorityQueueReceiversTypeDeducer;  template<class ...Inputs> struct MultiPriorityQueueReceiversTypeDeducer<std::tuple<Inputs...>> {

using type = MultiPriorityQueueReceivers<Inputs...>; };  template<class TupleInputs>

using MultiPriorityQueueReceiversTypeDeducer_t = typename MultiPriorityQueueReceiversTypeDeducer<TupleInputs>::type;

template<size_t Separator, class ...AllTypes> using MPQR = MultiPriorityQueueReceiversTypeDeducer_t<hh::tool::Inputs<Separator, AllTypes...>>;

It can then be used to create an abstraction to create a task that uses a priority queue instead of a normal queue:

template<size_t Separator, class ...AllTypes> class AbstractPriorityQueueTask : public hh::AbstractTask<Separator, AllTypes...> { public:

explicit AbstractPriorityQueueTask(std::string const &name, size_t const numberThreads, bool const automaticStart)

: hh::AbstractTask<Separator, AllTypes...>( std::make_shared<hh::core::CoreTask<Separator, AllTypes...>>( this, name, numberThreads, automaticStart,

std::make_shared<hh::core::implementor::DefaultSlot>(), std::make_shared<MPQR<Separator, AllTypes...>>(),

std::make_shared<hh::tool::DME<Separator, AllTypes...>>(this), std::make_shared<hh::core::implementor::DefaultNotifier>(),

std::make_shared<hh::tool::MDS<Separator, AllTypes...>>() ) ) {} };

Thanks to the helper we have just defined we can deduct the right type from the template parameters of the AbstractPriorityQueueTask.

Then, like any other task we define a conreate one: class IntIntPriorityQueueTask : public AbstractPriorityQueueTask<1, int, int> { public:

IntIntPriorityQueueTask() : AbstractPriorityQueueTask("IntPriorityQueue", 1, false) {} void execute(std::shared_ptr<int> data) override {

std::cout << *data << std::endl; this->addResult(data); } };  We can do exactly the same to define a state manager that uses a priority queue:

template<size_t Separator, class ...AllTypes> class PriorityQueueStateManager : public hh::StateManager<Separator, AllTypes...> { public:

explicit PriorityQueueStateManager(std::shared_ptr<hh::AbstractState<Separator, AllTypes...>> const &state,

std::string const &name, bool const automaticStart) : hh::StateManager<Separator, AllTypes...>(

std::make_shared<hh::core::CoreStateManager<Separator, AllTypes...>>( this, state, name, automaticStart,

std::make_shared<hh::core::implementor::DefaultSlot>(), std::make_shared<MPQR<Separator, AllTypes...>>(),

std::make_shared<hh::tool::DME<Separator, AllTypes...>>(state.get()), std::make_shared<hh::core::implementor::DefaultNotifier>(),

std::make_shared<hh::tool::MDS<Separator, AllTypes...>>() ), state ) {} };  // And a compatible state:

class IntState : public hh::AbstractState<1, int, int> { public: void execute(std::shared_ptr<int> data) override { std::cout << *data << std::endl;

this->addResult(data); } };  Then finally we can create graphs using these new tasks: hh::Graph<1, int, int> g;

// auto task = std::make_shared<IntIntPriorityQueueTask>(); // g.inputs(task); // g.outputs(task);  auto sm =

std::make_shared<PriorityQueueStateManager<1, int, int>>( std::make_shared<IntState>(), "Priority State Manager", false);  g.inputs(sm);

g.outputs(sm);  for (int i = 100; i >= 0; --i) { g.pushData(std::make_shared<int>(i)); }  g.executeGraph(); g.finishPushingData();

g.waitForTermination();

And even though we push ints from 100 to 0, they are printed from the state manager / task from 0 to 100 proving the correct usage of the priority queue.

Creating a new type of node (advanced users)

If the existing nodes do not meet the functionality that you are looking for, then it is possible to create new nodes.

To create a new node, we need to create 1) a core and 2) create the corresponding API.

Both of the API and the core are built following the template method behavioral pattern.

To create a new core and API it suffices to create your classes by inheriting from the different abstractions:  For the core:

NodeAbstraction: Base node definition GraphNodeAbstraction: Base graph definition TaskNodeAbstraction: Base task definition

StateManagerNodeAbstraction: Base state manager definition ExecutionPipelineNodeAbstraction:Base Execution pipeline definition

NotifierAbstraction: Sending message notification abstraction SlotAbstraction: Receiving message notification abstraction

ReceiverAbstraction: Receiving data abstraction SenderAbstraction: Sending data abstraction

ClonableAbstraction: Clonable abstraction for duplicating a node when creating clone graph in an execution pipeline

[Any]GroupableAbstraction: Groupable abstraction to duplicate a node to form a group (one abstraction is templatized)

CleanableAbstraction: Interface for calling API nodes that can redefine the clean method

CopyableAbstraction: Interface for calling API nodes that can redefine the copy method

ExecutionAbstraction: Interface for calling API nodes that can redefine the execute method

PrintableAbstraction: Interface used to determine if the node should be visited by the printer and colored   For the API:

MultiReceivers: Allows for a node to have the info to receive multiple types of data

MultiSenders: Allows for a node to have the info to send multiple types of data CanTerminate: Defines the canTerminate method

Cleanable: Defines the clean method Copyable: Defines the copy method Execute: Defines the execute method for a type

MultiExecute: Defines the execute method for multiple types Node: Defines the base information for a node

TaskNode: Defines the base information for a task

We have also created interfaces to manage the input data and the output data of the cores independently:

ExecutionPipelineInputsManagementAbstraction ExecutionPipelineOutputsManagementAbstraction TaskInputsManagementAbstraction

TaskOutputsManagementAbstraction GraphInputsManagementAbstraction GraphOutputsManagementAbstraction  They have two main purposes:

Split the input / output parts of the cores Simplify the access to the input / output types to simplify the inheritance patterns

The last point is fairly important, because we have to split properly the <Separator, â¦AllTypes> template parameters:

For the input types: we have defined hh::tool::Inputs<Separator, AllTypesâ¦> to help acquire them (wrapped in a std::tuple),

For the output types: we have defined hh::tool::Outputs<Separator, AllTypesâ¦> to help acquire them (wrapped in a std::tuple).

From these helpers we can deduce the real types, for example:

/// @brief Type alias for an TaskInputsManagementAbstraction from the list of template parameters template<size_t Separator, class ...AllTypes>

using TIM = tool::TaskInputsManagementAbstractionTypeDeducer_t<tool::Inputs<Separator, AllTypes...>>;

From these abstractions, you can create new nodes and because they use the Hedgehog abstractions they should be compatible with the rest of the library.

Conclusion In this tutorial we have seen how it is possible to extend the Hedgehog library by:  Creating a new node by deriving the API,

Creating a new node by creating a new implementor and customizing the node and core accordingly,

Creating a new type of node vy creating a core and node from the different abstractions.          Hedgehog Tutorials

Tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

</link8>

<link9>
Moving from Hedgehog v.2 to Hedgehog v.3 | Hedgehog Tutorials                      Hedgehog Tutorials

AboutPreambleTutorial 1 - Simple Hadamard ProductTutorial 2 - Hadamard Product with Managed StateTutorial 3 - Parallel ReductionTutorial 4 - Matrix Multiplication with cycleTutorial 5 - Matrix Multiplication on NVIDIA GPU with memory managementTutorial 6 - Matrix Multiplication on multiple NVIDIA GPUsTutorial 7 - Compile-time analysisTutorial 8 - Extensibility in HedgehogProfiling toolsMoving from Hedgehog v.2 to Hedgehog v.3

Moving from Hedgehog v.2 to Hedgehog v.3   There are few differences between Hedgehog v.2 and Hedgehog v.3.

This page is made to give you few pointers if you encounter some difficulties when porting your project to the newest version of the library.

If your problem is not covered in these few points, then feel free to contact us. Content  Template arguments definition Graph API Can terminate API

State Manager / State Memory manager Execution pipeline   Template arguments definition

The biggest change between Hedgehog v.2 and Hedgehog v.3 is the addition of multiple outputs.

A node (a task or a graph for example), can now have multiple input types and multiple output types.

To express this change, the template argument list has changed. Before the API looked like this: Node<Output, Input1, Input2, Input3>

This defines a node that accepts values of type Input1, Input2, and Input3 and sends values of type Output. The new API now looks like this:

Node<Separator, Type1, Type2, Type3, ...>

The Separator marks the number of inputs for the node, followed the input types. After the Separatorth input, then the remaining types are interpretted as output types.

For example, if a task is defined in Hedgehog v.2 as follows: class IntDoubleCharToFloat : public hh::AbstractTask<float, int, double, char>

It is now defined in Hedgehog v.3 : class IntDoubleCharToFloat : public hh::AbstractTask<3, int, double, char, float>

It reads: the three first types (int, double, and char) are the input types of the task, and the task has only one output type float. The graph:

class NewGRaph : public hh::Graph<3, A, B, C, D, E, F>

is a graph that accepts the types A, B, and C and produces the types D, E, and F. This configuration is not expressible in Hedgehog v.2.  Graph API

Because of the addition of multiple outputs, the connections in a graph are slightly different.

In Hedgehog v.2, there were 3 methods to create edges in Hedgehog: template<HedgehogMultiReceiver UserDefinedInput>

void input(std::shared_ptr<UserDefinedInput> input); // To set a node as input of the graph for all common types

template<HedgehogSender UserDefinedOutput>

void output(std::shared_ptr<UserDefinedOutput> output); // To set a node as output of the graph for all common types

template<HedgehogSender UserDefinedSender, HedgehogMultiReceiver UserDefinedMultiReceiver>

void addEdge(std::shared_ptr<UserDefinedSender> from, std::shared_ptr<UserDefinedMultiReceiver> to); // To draw an edge between two nodes for the only possible common type



In the newest API, we have added additional methods to handle the various types of inputs and outputs. One mechanism to accept all valid inputs and outputs between nodes and another specify the specific input/output.

// Set a node of type InputNode_t as input of the graph for the type InputDataType template< class InputDataType,

tool::CompatibleInputNodeForAType<InputDataType, typename core::GIM<Separator, AllTypes...>::inputs_t> InputNode_t >

void input(std::shared_ptr<InputNode_t> inputNode);  // Set a node of type OutputNode_t as output of the graph for the type OutputType template<

class OutputType, tool::CompatibleOutputNodeForAType<OutputType, typename core::GOM<Separator, AllTypes...>::outputs_t> OutputNode_t >

void output(std::shared_ptr<OutputNode_t> outputNode);

// Create an edge between the nodes of type SenderNode_t and ReceiverNode_t for the type CommonType template< class CommonType,

tool::SenderNodeForAType<CommonType> SenderNode_t, tool::ReceiverNodeForAType<CommonType> ReceiverNode_t >

void edge(std::shared_ptr<SenderNode_t> sender, std::shared_ptr<ReceiverNode_t> receiver);

// Set a node of type InputNode_t as input of the graph for all the common types between the node's input types and the graph's input types

template<tool::CompatibleInputNode<typename core::GIM<Separator, AllTypes...>::inputs_t> InputNode_t>

void inputs(std::shared_ptr<InputNode_t> inputNode);

// Set a node of type OutputNode_t as output of the graph for all the common types between the node's output types and the graph's output types

template<tool::CompatibleOutputNode<typename core::GOM<Separator, AllTypes...>::outputs_t> OutputNode_t>

void outputs(std::shared_ptr<OutputNode_t> outputNode);

// Create an edge between the nodes of type SenderNode_t and ReceiverNode_t all the common types between the sender's output types and the receiver's input types

template<tool::SenderNode SenderNode_t, tool::ReceiverNode ReceiverNode_t>

void edges(std::shared_ptr<SenderNode_t> sender, std::shared_ptr<ReceiverNode_t> receiver);   Can terminate API

The canTerminate method used in nodes to stop the computation early is now const. The signature was: virtual bool canTerminate();  and now is:

[[nodiscard]] virtual bool canTerminate() const;   State Manager / State

The state manager constructor has slightly changed, because a hh::AbstractState is mandatory to create a state manager, it has been put as the first constructor argument.

The constructor setting the name and the state has been changed from: StateManager(std::string_view const name, // Name

std::shared_ptr<StateType> const state, // State bool automaticStart = false); // Set the state manager to not start with a nullptr data  to:

explicit StateManager( std::shared_ptr<AbstractState<Separator, AllTypes...>> state, // State

std::string const &name = "State manager", // Name [default="State manager"]

bool const automaticStart = false); // Set the state manager to not start with a nullptr data

Furthermore, the hh::AbstractState method to send data to the successor node[s] has been changed from push() to addResult() to be more coherent with the rest of the library.

Memory manager The memory manager / managed data has been changed to be more explicit. ManagedMemory / MemoryManager

The MemoryData has been renamed ManagedMemory by symmetry to the MemoryManager name. To create a ManagedMemory, before we use a CRTP constructs:

template<class ManagedMemory> class MemoryData : public std::enable_shared_from_this<MemoryData<ManagedMemory>>;  // which translate to

class A : public hh::MemoryData<A>;  // When creating a type A usable by a MemoryManager

Now, to create a type actionable by a MemoryManager a simple inheritance is enough: class A : public hh::ManagedMemory;

This change is due to the relaxation of the rule saying that the type of the managed memory attached to a node should be the same as a nodeâs output type.

Now the type managed could be any type (at the moment it inherits from hh::ManagedMemory).

The counterpart is, the MemoryManager returns a *std::shared_ptr* when *getManagedMemory()* is used in compatible nodes (and not the *real* type as before, however *std::dynamic_pointer_cast* can be used to recover it: *auto a = std::dynamic_pointer_cast\<A\>(this->getManagedMemory())*).

API changes    Hedgehog v.2 Hedgehog v.3 Documentation     used() postProcess()

Mechanism called by Hedgehog when the node returns the memory before it is tested for being recycled (for example in the case the ManagedMemory is returned to the MemoryManager multiple times before being recycled (based on return of canBeRecycled) and sent back to the Pool).

recycle() clean()

Clean the ManagedMemory, the method is called right before sending it back to the pool in order to help having consistent data in the pool at any time.

reuse preProcess() Pre-process the data when acquired through getManagedMemory() to do specific allocation or data setup.     Execution pipeline

The constructor for the execution pipeline has been rethought to be simpler to use. There are now two constructors:  AbstractExecutionPipeline(

std::shared_ptr<Graph<Separator, AllTypes...>> graph, size_t const &numberGraphs, std::string const name = "Execution pipeline");

AbstractExecutionPipeline( std::shared_ptr<Graph<Separator, AllTypes...>> const graph, std::vector<int> const &deviceIds,

std::string const name = "Execution pipeline")

For both, the first argument is the graph that will be duplicated and the last is the execution pipelineâs name. The second argument is:

numberGraphs: The number of graphs in the execution pipeline. The device ids are automatically generated in sequence and attached to the graphs. So, if numberGraphs = 5, there are 4 clones + the base graph, and the device ids generated are 0, 1, 2, 3, and 4.

deviceIds: The devices ids attached to the graphs in the execution pipeline. The number of graphs in the execution pipeline is deduced from the number of given device ids. If the given vector is [4, 5, 6], the base graph is cloned twice (for a total of 3 graphs), and the device ids 4, 5, and 6 are attached to each of the graphs.

Hedgehog Tutorials

Tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

</link9>

<link10>
Tutorial 3 - Parallel Reduction | Hedgehog Tutorials                      Hedgehog Tutorials

AboutPreambleTutorial 1 - Simple Hadamard ProductTutorial 2 - Hadamard Product with Managed StateTutorial 3 - Parallel ReductionTutorial 4 - Matrix Multiplication with cycleTutorial 5 - Matrix Multiplication on NVIDIA GPU with memory managementTutorial 6 - Matrix Multiplication on multiple NVIDIA GPUsTutorial 7 - Compile-time analysisTutorial 8 - Extensibility in HedgehogProfiling toolsMoving from Hedgehog v.2 to Hedgehog v.3

Tutorial 3 - Parallel Reduction   Content  Goal Computation Tasks Graph Performance Conclusion   Goal

The goal of this tutorial is to propose an implementation of a parallel reduction algorithm.

In it, we showcase the usage of doing a fine grain computation and the cleaning API.

Additionally, we present how we can reuse a graph for multiple computations.  Computation

The principle of this algorithm is to reduce a collection of data (here a vector of ints) down to a single value with a specific operation.

This operation needs to be associative and commutative in nature.

A naive implementation would be to apply this operation in all elements in the collection consecutively.

We would like to propose a parallel implementation, our strategy is to decompose the vector to process small parts of it.

The parts are then reduced in parallel producing partial results. These are then reduced down to a single result value.

The input vector is considered as read-only, and wonât be writte too. We propose the following implementation:

Decompose the vector into parts (VectorDecomposition), Reduce these vectors down to partial results (ReductionTask),

Do the reduction of the partial results (FinalReductionTask).   Computation tasks Vector Decomposition We consider the vector as read-only.

In order to avoid extra copies or constructions of smaller vectors, the task produces a pair of iterators.

The iterators represents the range [begin, end] that need to be reduced. These ranges will be processed in parallel in the next task.

Below is the task definition: template<class DataType> class VectorDecomposition : public hh::AbstractTask<1, std::vector<DataType>,

std::pair<typename std::vector<DataType>::const_iterator, typename std::vector<DataType>::const_iterator>>;

The decomposition strategy is implemented as: void execute(std::shared_ptr<std::vector<DataType>> v) override { if (v->size() < blockSize_) {

throw std::runtime_error("The number of blocks is larger than the given vector of data."); } if (v->empty()) {

finalReductionType_->numberReductedBlocks(1); this->addResult( std::make_shared<

std::pair<typename std::vector<DataType>::const_iterator, typename std::vector<DataType>::const_iterator>>( v->cbegin(), v->cend())); } else {

finalReductionType_->numberReductedBlocks((size_t) std::ceil((double) v->size() / (double) (blockSize_))); auto begin = v->begin();

auto endIt = v->begin(); long endPosition = 0; while (endIt != v->end()) {

endPosition = (long) std::min((size_t) endPosition + blockSize_, v->size()); endIt = v->begin() + endPosition;

this->addResult(std::make_shared<std::pair< typename std::vector<DataType>::const_iterator,

typename std::vector<DataType>::const_iterator>>(begin, endIt)); begin = endIt; } } }  Main parallel reduction task

The parallel reduction is meant to reduce a range of data from the vector down to a single value.

In the main case, we do the reduction by calling std::reduce on the range of data with the lambda given by the end-user. this->addResult(

std::make_shared<DataType>(std::reduce(data->first + 1, data->second, *(data->first), lambda_)) );

We want to do this in parallel, so we create a group of tasks by setting the number of threads attached to the task >1 and implementing the copy function:

ReductionTask(size_t const numberThreads, std::function<DataType(DataType const &, DataType const &)> lambda) : hh::AbstractTask< 1,

std::pair<typename std::vector<DataType>::const_iterator, typename std::vector<DataType>::const_iterator>, DataType>

("Reduction task", numberThreads), lambda_(std::move(lambda)) {}  std::shared_ptr<hh::AbstractTask< 1,

std::pair<typename std::vector<DataType>::const_iterator, typename std::vector<DataType>::const_iterator>, DataType>> copy() override {

return std::make_shared<ReductionTask<DataType>>(this->numberThreads(), lambda_); }

The lambda, given as a parameter, is the operation that will be applied to each element to reduce them. Final reduction task

The purpose of this task is to reduce the partial results from the previous ReductionTask down to a single value.

We have chosen to use a single-threaded task for this implementation because:  The processing is lightweight compared to the ReductionTaskâs one,

We didnât want to pay the cost of synchronization

When the VectorDecomposition task gets a vector it updates the FinalReductionTaskâs number of partial results it needs to process.

This only works if we wait for the computation to go through before we send another input vector of data.

In addition, before processing another input we need to reset the attributes of the task. This is why we have overloaded the clean method.

void clean() override { stored_ = nullptr; numberReductedBlocks_ = 0; }  This is meant to clean the task to be able to process a new computation.

The other tasks do not maintain anything to do their computation, that is why we have not overloaded the clean method.

Alternatively, a more efficient methodology would use a unique identifier to mark each vector. This would be used by the FinalReductionTask to identify which data point belongs to which, allowing multiple vectors to be reduced in parallel. However for the sake of this example, we want to demonstrate the cleaning behavior.

Graph - Multiple computation - Graph cleaning

The way we use the graph is slightly different from the one used in other tutorials because we want to reuse it for multiple computations.

Usually, the sequence of operation for a graph is: 1) Instantiate the graph, 2) Build the graph, 3) Execute the graph, 4) Push the inputs,

5) Indicate no more input is sent to the graph (that start the graph termination), 6) Loop over the produced results,

7) Wait for the graph to fully terminates. Here, we follow this logic: 1) Instantiate the graph, 2) Build the graph, 3) Execute the graph,

4) For each input vector 1) Push an input data, 2) Get the result, 3) Clean the graph,

5) Indicate no more input is sent to the graph (starts the graph termination), 6) Wait for the graph to fully terminates.

We are reusing the graph: for a given range size, we reduce multiple vectors. This works because we know that for one input given we have one output.

If we were to wait for n results we would need to call n times the graph::getBlockingResult() method.

Looping over the output results with a while loop (as presented in other tutorials) wonât work because finishPushingData is not invoked before getting the output results (the while loop never breaks because the graph would only return nullptr when it is terminated).

Performance

To make the algorithm coarse, we decompose the input data into ranges and process each range in parallel. This ensures there is sufficient data to compensate for Hedgehogâs latency when sending data in the dataflow.

Additionally, the coarseness of the data has a huge impacts on the performance depending on your computer.

To present some performance results and to showcase these impacts we have run different experiments 20 times each with different input data sizes and range sizes.

We compute the average end-to-end computation time in nanoseconds and the standard deviation.

To compare these results together, we have divided the average computation time by the number of data in the input vector.

On a test computer with an Intel(R) Xeon(R) Silver 4114 CPU @ 2.20GHz with 40 logical cores (20 physical) and 196 GB memory ram we have the following results:

The color scheme is chosen as follows: green for the minimum value, yellow for the 20th percentile, and red for the maximum value.

The first remark is the speedup between the maximum value and the minimum value is about 1250x !

Then, we see that the best performance is neither too small nor too big.

The first is limited by the latency (cost of sending data between nodes) compared to the cost of the computation.

The second is limited due to not have sufficient data flowing through the graph and will not benefit from the available parallelism on this computer.

To generate the dot files we execute the following code: { auto v = std::make_shared<std::vector<DataType>>(131072, 1);

ParallelReductionGraph<DataType> graph(addition, 256, std::thread::hardware_concurrency()); graph.executeGraph(); graph.pushData(v);

graph.finishPushingData(); graph.waitForTermination();

graph.createDotFile("131072_256.dot", hh::ColorScheme::EXECUTION, hh::StructureOptions::QUEUE); }  {

auto v = std::make_shared<std::vector<DataType>>(16777216, 1);

ParallelReductionGraph<DataType> graph(addition, 524288, std::thread::hardware_concurrency()); graph.executeGraph(); graph.pushData(v);

graph.finishPushingData(); graph.waitForTermination();

graph.createDotFile("16777216_524288.dot", hh::ColorScheme::EXECUTION, hh::StructureOptions::QUEUE); }

We do not generate a dot representation for the graph each time because we reuse it for multiple computations. The dot generations are:

For the worst performance (131072 vector size and 256 range size)    For the best performance (16777216 vector size and 524288 range size)

Studying the dot files generated tells us primarily two things. First, in both cases the vector decomposition task is the primary bottleneck, so improvements for the tested vector size should be done within this task. Second, the MQS (Max Queue Size) provides us some insights. The MQS represents the maximum size that the taskâs input queue for the defined type reached throughout the entire execution. In both examples, this value is 1 for the input of the reduction task, which indicates that there was sufficient parallelism to keep up with the rate at which the vector decomposition task was producing data. This is one way to interpret this graph, and is often an excellent way to identify bottlenecks and where to focus your efforts when applying optimizations.

Conclusion In this tutorial we have seen:  The importance of data decomposition in Hedgehog and how to tackle parallelism,

How to clean a graph to reuse it for multiple computation.          Hedgehog Tutorials

Tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

</link10>

<link11>
Tutorial 6 - Matrix Multiplication on multiple NVIDIA GPUs | Hedgehog Tutorials                      Hedgehog Tutorials

AboutPreambleTutorial 1 - Simple Hadamard ProductTutorial 2 - Hadamard Product with Managed StateTutorial 3 - Parallel ReductionTutorial 4 - Matrix Multiplication with cycleTutorial 5 - Matrix Multiplication on NVIDIA GPU with memory managementTutorial 6 - Matrix Multiplication on multiple NVIDIA GPUsTutorial 7 - Compile-time analysisTutorial 8 - Extensibility in HedgehogProfiling toolsMoving from Hedgehog v.2 to Hedgehog v.3

Tutorial 6 - Matrix Multiplication on multiple NVIDIA GPUs   Content  Goal Computation Graph as node Multi GPU Computation Graph Representation

Conclusion   Goal The goal of this tutorial is to demonstrate how to bundle a graph, and use it within an execution pipeline across multiple GPUs.

Computation The data structure, tasks, state, state manager and decomposition strategy are reused from tutorial 5.

In Hedgehog, a graph is associated with a device. If no accelerator is used, the device id stored in the graph is not used.

If an accelerator, such as a GPU, is used, all the tasks of a graph are associated to the same device; i.e., there is only 1 device Id per graph.

Because we want to split the computation into multiple GPUs we need:  To create a graph per GPU,

To decompose the data and distribute it to the graphs.  The decomposition strategy for this computation follows these rules:

Traversal for Matrix A is column-by-column, and matrix B is row-by-row, as shown in tutorial 5,

The matching columns of matrix A and rows of matrix B are sent to the same GPU in a round-robin way for multiple GPUs.  Example Matrix A:

GPU / Column 0 1 2 3 4 5 6     0 x Â Â x Â Â x   1 Â x Â Â x Â Â   2 Â Â x Â Â x Â    Example Matrix B:    GPU / Row 0 1 2 3 4 5 6     0 x Â Â x Â Â

x   1 Â x Â Â x Â Â   2 Â Â x Â Â x Â    Therefore, all of column 0 for matrix A, and row 0 for matrix B will be sent to GPU 0.

This strategy eliminates the need to communicate between GPUs as all the data is resident on the same GPU when multiplying the matrix blocks.

Graph as node A Hedgehog Graph is a node that can be added into any other graph just like other nodes, like a task.

This is useful when developing a general purpose graph for others to use or defining functionality specific to a device, such as CUDA GPUs.

In this tutorial, the âinside graphâ holding all the âCUDA tasksâ is created as follows: template<class MatrixType>

class CUDAComputationGraph : public hh::Graph< 2, MatrixBlockData<MatrixType, 'a', Order::Column>, MatrixBlockData<MatrixType, 'b', Order::Column>,

MatrixBlockData<MatrixType, 'p', Order::Column> > { public:

CUDAComputationGraph(size_t n, size_t m, size_t p, size_t blockSize, size_t numberThreadProduct) : hh::Graph< 2,

MatrixBlockData<MatrixType, 'a', Order::Column>, MatrixBlockData<MatrixType, 'b', Order::Column>, MatrixBlockData<MatrixType, 'p', Order::Column>

>("GPU Computation Graph") {  // Nodes creation auto copyInATask = std::make_shared<CudaCopyInGpu<MatrixType, 'a'>>(pBlocks, blockSize, n);

auto copyInBTask = std::make_shared<CudaCopyInGpu<MatrixType, 'b'>>(nBlocks, blockSize, m); [...]  // Graph Creation this->inputs(copyInATask);

this->inputs(copyInBTask); [...] } };  A note, we do not need to create a specific class for the graph, we could use a graph instance directly.

In main, the graph needs to be instantiated, and linked to other nodes.

It is not possible to modify a graph once it has been linked to another node. Once a graph has been inserted inside of another, then that graph is marked as inside and can no longer be modified or interacted with when using the Hedgehog API.

For example the following code would not compile: #include <hedgehog/hedgehog.h>  class ItoITask : public AbstractTask<1, int, int>{ public:

void execute(std::shared_ptr<int> ptr) override { this->addResult(ptr); } };   int main (){

auto outerGraph = std::make_shared<Graph<int, int>>("Outer graph"); auto insideGraph = std::make_shared<Graph<int, int>>("Inside graph");  auto

i1 = std::make_shared<ItoITask>(), i2 = std::make_shared<ItoITask>(), o1 = std::make_shared<ItoITask>(), o2 = std::make_shared<ItoITask>();

insideGraph->inputs(i1); insideGraph->edges(i1, i2);  outerGraph->inputs(o1); outerGraph->edges(o1, insideGraph); outerGraph->edges(insideGraph, o2);

outerGraph->outputs(o2);  // The graph is modified after it has been linked insideGraph->outputs(i2);  outerGraph->executeGraph();

outerGraph->pushData(std::make_shared<int>(1)); outerGraph->finishPushingData(); outerGraph->waitForTermination(); }

To correct it the call to âoutputâ has to be moved: #include <hedgehog/hedgehog.h>  class ItoITask : public AbstractTask<int, int>{ public:

void execute(std::shared_ptr<int> ptr) override { this->addResult(ptr); } };   int main (){

auto outerGraph = std::make_shared<Graph<int, int>>("Outer graph"); auto insideGraph = std::make_shared<Graph<int, int>>("Inside graph");  auto

i1 = std::make_shared<ItoITask>(), i2 = std::make_shared<ItoITask>(), o1 = std::make_shared<ItoITask>(), o2 = std::make_shared<ItoITask>();

insideGraph->inputs(i1); insideGraph->edges(i1, i2); insideGraph->outputs(i2);  outerGraph->inputs(o1); outerGraph->edges(o1, insideGraph);

outerGraph->edges(insideGraph, o2); outerGraph->outputs(o2);  outerGraph->executeGraph(); outerGraph->pushData(std::make_shared<int>(1));

outerGraph->finishPushingData(); outerGraph->waitForTermination(); }   Multi GPU Computation

To execute across multi-GPUs, Hedgehog has a specialized node called an Execution Pipeline. It will:

Duplicate the graph and associate each of them to a specific device Id, Distribute data over the graphs.

So, to create an Execution Pipeline, it needs:  The number of times the graph is to be duplicated, The device ids the graphs will be associated with,

An overload of the âsendToGraphâ method, that define the way the data is distributed to the graphs (one for each input type).

template<class MatrixType> class MultiGPUExecPipeline : public hh::AbstractExecutionPipeline< 2, MatrixBlockData<MatrixType, 'a', Order::Column>,

MatrixBlockData<MatrixType, 'b', Order::Column>, MatrixBlockData<MatrixType, 'p', Order::Column> > { private: size_t numberGraphDuplication_ = 0;

public: MultiGPUExecPipeline(std::shared_ptr<hh::Graph< 2,

MatrixBlockData<MatrixType, 'a', Order::Column>, MatrixBlockData<MatrixType, 'b', Order::Column>, MatrixBlockData<MatrixType, 'p', Order::Column>

>> const &graph, std::vector<int> const &deviceIds) : hh::AbstractExecutionPipeline< 2,

MatrixBlockData<MatrixType, 'a', Order::Column>, MatrixBlockData<MatrixType, 'b', Order::Column>, MatrixBlockData<MatrixType, 'p', Order::Column>

>(graph, deviceIds, "Cuda Execution Pipeline"), numberGraphDuplication_(deviceIds.size()) {} virtual ~MultiGPUExecPipeline() = default;

bool sendToGraph( std::shared_ptr<MatrixBlockData<MatrixType, 'a', Order::Column>> &data, size_t const &graphId) override {

return data->colIdx() % numberGraphDuplication_ == graphId; }  bool sendToGraph(

std::shared_ptr<MatrixBlockData<MatrixType, 'b', Order::Column>> &data, size_t const &graphId) override {

return data->rowIdx() % numberGraphDuplication_ == graphId; } };

The execution pipeline is also used like any other nodes in Hedgehog, it has to be instantiated and added into a graph. // GPU Graph

auto cudaMatrixMultiplication = std::make_shared<CUDAComputationGraph<MatrixType>>(n, m, p, blockSize, numberThreadProduct);  // Execution Pipeline

auto executionPipeline = std::make_shared<MultiGPUExecPipeline<MatrixType>>(cudaMatrixMultiplication, deviceIds);  // Send the blocks to GPU Graph

matrixMultiplicationGraph.edges(taskTraversalA, executionPipeline); matrixMultiplicationGraph.edges(taskTraversalB, executionPipeline);

// Get back the blocks out the GPU Graph matrixMultiplicationGraph.edges(executionPipeline, stateManagerPartialComputation);   Graph Representation

Here is the final graph:   Conclusion We have seen in this tutorial:  How to bundle a task into a reusable or shareable graph,

How to manage computation into multiple GPUs with the Execution Pipeline.          Hedgehog Tutorials

Tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

</link11>

<link12>
Tutorial 2 - Hadamard Product with Managed State | Hedgehog Tutorials                      Hedgehog Tutorials

AboutPreambleTutorial 1 - Simple Hadamard ProductTutorial 2 - Hadamard Product with Managed StateTutorial 3 - Parallel ReductionTutorial 4 - Matrix Multiplication with cycleTutorial 5 - Matrix Multiplication on NVIDIA GPU with memory managementTutorial 6 - Matrix Multiplication on multiple NVIDIA GPUsTutorial 7 - Compile-time analysisTutorial 8 - Extensibility in HedgehogProfiling toolsMoving from Hedgehog v.2 to Hedgehog v.3

Tutorial 2 - Hadamard Product with Managed State   Content  Goal Computation Data structure State and State Manager Task Graph Conclusion

Goal

The second tutorial aims to reuse the Hadamard (element-wise) product of two matrices A and B from tutorial 1 to introduce the concept of multiple inputs, state, and state manager.

Here is the base API that will be presented in this tutorial:  Manage the state of the computation, Define a task with multiple inputs.   Computation

The computation is decomposed as follows:  Decompose the matrices into blocks (inside the graph),

Do the element-wise product of A and B, and store the result into C.

Because the decomposition of A, B, and C takes place within the graph, it is required to manage the state of the computation to be able to build the correct triplet for blocks A, B, and C. This is because the order in which blocks flow through the graph are non-determinstic.

Data structure We will use the same data structures as tutorial 1:  MatrixData<T, Id, Order>: A matrix,

MatrixBlockData<T, Id, Order>: A matrix block, TripleMatrixBlockData<T, Order>: The corresponding block from matrix A, matrix B and matrix C.

These data structures are specialized with the following elements:  Type: The type of the matrix elements, Id: The matrix identifier, a, b, or, c,

Ord: The way the matrix is ordered, row based, or, column based.   State and State Manager

While tasks are meant to achieve computations, we added a special type of node for managing the state of computations.

In Hedgehog, the management of status is localized, being only responsible for handling the state between connected nodes. There is no built-in representation of the global state in the Hedgehog API.

This type of node is represented by the StateManager class.

Technically a StateManager is a task limited to only one thread, requiring a State object at construction.

State is an object used to express the data synchronization strategy of a set of nodes handled by a state manager.

For example, we used blocks to parallelize the computation in the previous tutorial. MatrixData A, B, and C are fed into the algorithm.

Input tasks (MatrixRowTraversalTask) will decompose them into blocks.

The first step of the algorithm will be to multiply these blocks of matrices together.

The problem is that elements within A should be multiplied by their corresponding elements in B and stored in the correct location in C. The order in which these blocks are sent from the MatrixRowTraversalTask is non-deterministic, so we need to wait until corresponding blocks are received before sending them for element-wise multiplication.

In order to manage the blocks coming from the decomposition tasks and forming the compatible pairs we use a StateManager and a State.

The State holds a representation of the grid of blocks, retains them until a compatible pair is possible, forms the pair of blocks and sends it to the HadamardProduct task.

To manage the state of computation two C++ objects are needed:

An abstract state: The object that will represent the state itself. It will hold the data structures that are needed to manage the state of the computation.

A state manager task: A Hedgehog node that will execute the state with data sent to task and produce data sent from the state for the next task in the dataflow.

To demonstrate the usage of the state and state manager, the code of the BlockState will be explained.  State

In this computation, we want to form a triplet of blocks from the blocks of matrix A, matrix B, and matrix C.

To achieve that we create a class BlockState as follows: template<class Type, Order Ord> class BlockState : public hh::AbstractState< 3,

MatrixBlockData<Type, 'a', Ord>, MatrixBlockData<Type, 'b', Ord>, MatrixBlockData<Type, 'c', Ord>, TripletMatrixBlockData<Type, Ord>>;  We note here:

The declaration follows the same ordering as the AbstractTask, separator first then the list of types,

There are multiple input types: Nodes in Hedgehog can accept multiple inputs, such as the graph, state, or task.  The multiple inputs imply:

The node can accept data from nodes that produce one of its input types.

The different types of inputs are received and handled independently of the others.

Multiple execute method will need to be defined, one for each input type.

The order in which the input types are received are non-deterministic and will executed one at a time.

void execute(std::shared_ptr<MatrixBlockData<Type, 'a', Ord>> ptr) override { /*[...]*/ }

void execute(std::shared_ptr<MatrixBlockData<Type, 'b', Ord>> ptr) override { /*[...]*/ }

void execute(std::shared_ptr<MatrixBlockData<Type, 'c', Ord>> ptr) override { /*[...]*/ }

Contrary to the task, the state does not provide their results directly to another node, but their results are transferred to the state manager that will manage it.

Data is enqueued by the state by using the addResult method: void execute(std::shared_ptr<MatrixBlockData<Type, 'a', Ord>> ptr) override { /*[...]*/

this->addResult(triplet); }

In our example, we can receive any block (in any order) of matrix A, B or C, and we will produce a triplet of these blocks only if they correspond with each other: they represent the same part of the matrix.

When corresponding blocks are not available, a block is stored to await for the matching block(s) to arrive later.

For each type of matrix, we define a temporary storage for these blocks with accessors that permits the storage and receiving of these blocks.

We use this storage to test if a triplet of blocks is available and remove the blocks from the storage when they are pushed to the next task.

For the storage of blocks from matrix A we will have: private: // The temporary storage data structure

std::vector<std::shared_ptr<MatrixBlockData<Type, 'a', Ord>>> gridMatrixA_ = {};  // The getter

std::shared_ptr<MatrixBlockData<Type, 'a', Ord>> matrixA(size_t i, size_t j) { return gridMatrixA_[i * gridWidth_ + j]; }  // The setter

void matrixA(std::shared_ptr<MatrixBlockData<Type, 'a', Ord>> blockA){ gridMatrixA_[blockA->rowIdx() * gridWidth_ + blockA->colIdx()] = blockA; }

// The method to remove it void resetA(size_t i, size_t j){ gridMatrixA_[i * gridWidth_ + j] = nullptr; }

The computation will be almost the same for each of the input types: void execute(std::shared_ptr<MatrixBlockData<Type, 'a', Ord>> ptr) override {

std::shared_ptr<MatrixBlockData<Type, 'b', Ord>> blockB = nullptr; std::shared_ptr<MatrixBlockData<Type, 'c', Ord>> blockC = nullptr;

// We get the position of the block inside the grid of blocks auto rowIdx = ptr->rowIdx(), colIdx = ptr->colIdx();

// We get and test if the other corresponding blocks are available if((blockB = matrixB(rowIdx, colIdx)) && (blockC = matrixC(rowIdx, colIdx))){

// If they are we remove them from the data structure resetB(rowIdx, colIdx); resetC(rowIdx, colIdx); // We create the triplet

auto triplet = std::make_shared<TripletMatrixBlockData<Type, Ord>>(); triplet->a_ = ptr; triplet->b_ = blockB; triplet->c_ = blockC;

// We transfer it to the state manager this->addResult(triplet); }else{ // If not, we store the block matrixA(ptr); } }

With this code we achieve a synchronization point for matrices A, B, and C, which is independent of the traversal.

State is accessed synchronously by the state manager via locks that are built-in to the state.

This ensures that there will be no race conditions when calling the execute method.  State Manager

The state manager, is a type of node, that holds state.

The state manager, fired with an input type, will sequentially process the data in the following order:  lock the state,

call the state execute with the input data, gather the outputs from the state, add the outputs to its output edge unlock the state.

To note, multiple state managers are allowed to hold the same state instance, so itâs possible to share the state at different points in the graph.

Because itâs locked, the computation into a state should be as minimal and as fast as possible.

In this tutorial, we use Hedgehogâs default state manager, that is created as follows: // Declaring and instantiating the state and state manager

auto inputState = std::make_shared<BlockState<MatrixType, Ord>>(matrixA->numBlocksRows(), matrixA->numBlocksCols()); auto inputstateManager =

std::make_shared< hh::StateManager< 3,

MatrixBlockData<MatrixType, 'a', Ord>, MatrixBlockData<MatrixType, 'b', Ord>, MatrixBlockData<MatrixType, 'c', Ord>,

TripletMatrixBlockData<MatrixType, Ord> > >(inputState, "Block State Manager");   Computation task We reuse the same task as shown in tutorial 1.

The MatrixRowTraversalTask is used to produce the different blocks from each matrix, which are gathered and distributed for corresponding triplets by the state manager to the computation task.

Graph The graph from tutorial 1 is changed slightly to operate with receiving three types of MatrixData for A, B, and C.

Below is the graph construction, the connection to the input of the graph must match at least one of the task input(s) and the output of the graph must match the output of task output.

// Set The hadamard task as the task that will be connected to the graph inputs graphHadamard.inputs(taskTraversalA);

graphHadamard.inputs(taskTraversalB); graphHadamard.inputs(taskTraversalC);  // Link the traversal tasks to the input state manager

graphHadamard.edges(taskTraversalA, inputstateManager); graphHadamard.edges(taskTraversalB, inputstateManager);

graphHadamard.edges(taskTraversalC, inputstateManager);  // Link the input state manager to the hadamard product

graphHadamard.edges(inputstateManager, hadamardProduct);  // Set The hadamard task as the task that will be connected to the graph output

graphHadamard.outputs(hadamardProduct);  And here is the visualization:   Conclusion In this tutorial, we have demonstrated:  How to create state,

How to use the default state manager, How to use multiple input types.          Hedgehog Tutorials

Tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

</link12>

<link13>
Preamble | Hedgehog Tutorials                      Hedgehog Tutorials

AboutPreambleTutorial 1 - Simple Hadamard ProductTutorial 2 - Hadamard Product with Managed StateTutorial 3 - Parallel ReductionTutorial 4 - Matrix Multiplication with cycleTutorial 5 - Matrix Multiplication on NVIDIA GPU with memory managementTutorial 6 - Matrix Multiplication on multiple NVIDIA GPUsTutorial 7 - Compile-time analysisTutorial 8 - Extensibility in HedgehogProfiling toolsMoving from Hedgehog v.2 to Hedgehog v.3

Preamble   Introduction Thank you for your interest in this library.

The Hedgehog library aids developers in creating dataflow graphs. These dataflow graphs are used to implement algorithms that execute on heterogenous computers.

This preamble is made to present what Hedgehog is and its execution model.

For more details, please see our publications: (DOI: 10.1109/PAWATM51920.2020.00006).

The current version of Hedgehog is version 3, if you have used Hedgehog version 2 before we have a section to help you port your code.

Execution models Dataflow graph Hedgehog presents an algorithm under the form of a dataflow graph.

The nodes of the graph are the computational kernels and the vertices presents the flow of data. The graph is a logical bundle of nodes and edges.

In addition, a graph is a node in Hedgehog, it is possible to compose graphs together. A simple graph representation looks like this:

A, B, C, D, and E are the computational kernels, and T1, T2, T3, T4, T5, T6, and T7 are the different types of data flowing into the graph.

The graph is static and explicit. What is designed, is what is executed without transformation.

The data flowing through the edges are actually std::shared_ptr wrapping the data between the nodes.

If a node has multiple successors for a type, the std::shared_ptr is copied to each of the successors.

Hedgehogâs dataflow graphs can be created in many different ways and allow cycles. However, cycles must be handled with care, as presented in Tutorial 4 - Cycle resolution: CPU Matrix Multiplication.

The creation of such graphs in Hedgehog and its various abstractions are covered in detail within these tutorials.

Other conceptual differences between Hedgehog and other libraries are highlighted in this section. Threading model

By default, each computational node (task) is attached to one (or more) threads since its creation to its destruction. These threads are persistent to the computational node it is attached too, and do not traverse other nodes in the graph. Threads execute based on the prescence of data. If there is no data prescent, then the thread will enter a wait state, releasing CPU resources. By default, the thread will infinitely process data for that computational node until the connection to the computational node is disconnected and the data queue is empty.

The thread management is solely done by the OS; we rely on it and not on a scheduler to avoid extra computations and extra latency.

However, Hedgehog has a scheduler abstraction for customizing this behavior. Data pipelining

To gain performance, Hedgehog relies on data pipelining and thread group parallelism.

If computational nodes are executing independently and the output of some are inputs of others, you have inherent parallelism and computations overlap.

This can be used to effectively overlap different kinds of computations, for example IO with kernel execution. Additionally, a thread group can process data in parallel if there is sufficient data waiting to be processed.

This technique works best if big enough pieces of data are sent into the graph.

The latency (transfer time between two nodes) of the system is ~10 us in most cases.

Computational nodes for example have thread-safe queues (one per input type) protected by a mutex.

The mutex must be locked when data is sent to the task and acquired by the task, and then unlocked prior to executing on the data. In a thread group another thread can then acquire that mutex to fetch the next piece of data and work on different data in parallel.

We consider Hedgehog to be a coarse gain library, the nodes are not meant to do computations on a single value, but on blocks of data. Ideally, there will be sufficient computation on data to justify the costs of sending data. Fine-grained parallelism is often done within a node by applying various high performance techniques or calling optimized library functions on data, such as OpenCV, OpenBLAS, or FFTW libraries to name a few.

Understanding the performance impliciations of the Hedgehog graph can be visualized by taking advantage of its zero-overhead profiling tools

Main differences with a task graph model Hedgehog uses a static and explicit dataflow graph and does not follow the traditional task graph design.

Typical task graphs work as follows:

The library analyses an algorithm representation created by the end-user, may apply a transformation to it, and analyses the node dependencies.

Then, when a node is ready to be fired, the runtime system attaches the kernel to a thread from a pool thanks to a scheduler.

Then the output data are gathered and the following nodes are fired.

Hedgehog operates in a way that does not change its underlying dataflow graph structure. The way in which the user constructs the dataflow graph is not modified by Hedgehog and is exactly what is executed.

When the graph is executed, the computational nodes are attached to threads.

The threads stay bound to the nodes until there is no more data to be processed by the task (cf. Threading model and Task logic).

However, a thread wonât be executing at all times, it can enter a wait state if there is nothing to process, which frees up resources.

Once data arrives to a node, the thread is signaled to wake up by its predessor node so that it can fetch data from its queue, and then processes it (cf. Data pipelining). This procedure is handled by the operating system.

In this structure, Hedgehog does not operate with a scheduler, the node execution is only triggered by the arrival or the presence of data in its input queues.

Task logic Once attached to a thread the task follows this logic:  The steps in blue are the ones that can be customized by an end-user:

Initialize: executed once when the task is attached to the thread, Shutdown: executed once when the task is about to terminate,

Execute: the computational kernel implementation / what it executed when a piece of data is acquired by the task,

Can terminate: condition termination (Tutorial 4).  So, when a taskâs thread is attached, it:  Call initialize, If it can terminate:  Call shutdown

Notify successor node[s] for nodeâs termination Detach the thread Terminate

Enter a wait state until a piece of data is sent and the node is notified or gets notified by predecessor termination If it can terminate:

Call shutdown Notify successor node[s] for nodeâs termination Detach the thread Terminate   Lock an input queue

Get a piece of data out of an input queue Unlock the queue Call execute with the piece of data Go to 2

It is important to understand that a taskâs thread starts when the graph is executed.

It continues to run until all predecessor nodes are terminated and no input data is available (or the redefined canTerminate method returns true).

The termination of the graphâs input nodes is triggered when the end-user calls Graph::finishPushingData(). This will indicate to the input nodes that there is no longer data being sent into the graph.

The state managers works similarly to the task, but with a customized execute method:  lock the state,

call the stateâs execute method with the piece of data, wait for the state to finish processing the data,

gather all output data produced by the state, unlock the state, send the output data to the successor nodes.  Gain performance with Hedgehog Design

The first step to create a performant algorithm implementation is to use a pen and paper and decompose the algorithm into independent pieces.

Each of the pieces translates into a node in a Hedgehog graph. The edges represents the data needed to process a step in the algorithm.

The choice of the node abstraction is of importance, that is why the first three tutorials are meant to present the main abstractions.

Profiling tools

Once designed and implemented, we have added multiple tools that help to detect flaws in the design, showing bottlenecks and concurrency between the nodes.

The main tools have been showed to be costless, and we recommend to use it for every implementation.

This section covers the different profiling mechanisms. Structure of the tutorials

We have designed the tutorials to give a progressive explanations on the different tools and options available in the library:

Tutorial 1 explains how to build a basic graph with a basic task. Tutorial 2 introduces the state and state manager nodes for managing computations.

Tutorial 3 showcases the importance of data coarseness and how to clean a graph for multiple computations.

Tutorial 4 shows how to solve problems with cycles in Hedgehog. Tutorial 5 presents GPU computation on NVIDIA GPUs.

Tutorial 6 extends the previous tutorial by porting it to multiple-GPUs with an execution pipeline and using graph composition.

Tutorial 7 exposes the compile-time analysis tool library. Tutorial 8 demonstrate how Hedgehog can be extended.          Hedgehog Tutorials

Tutorials for the Hedgehog library, designed to aid in creating task graphs for algorithms to obtain performance across CPUs and multiple co-processors.

</link13>
</Website1>

</WEBSITES>

